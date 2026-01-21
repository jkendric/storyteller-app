import re
from typing import AsyncGenerator, Optional
from sqlalchemy.orm import Session

from app.models import Story, Episode, StoryCharacter, MemoryState
from app.models.story import StoryStatus
from app.services.llm_service import llm_service, ProviderManager
from app.services.memory_service import memory_service
from app.services.prompt_service import prompt_service, WORD_PRESETS
from app.config import get_settings

settings = get_settings()


class StoryService:
    """Service for story orchestration and episode generation."""

    async def generate_episode_stream(
        self,
        db: Session,
        story_id: int,
        guidance: Optional[str] = None,
        target_words: Optional[int] = None,
        use_alternate: bool = False,
    ) -> AsyncGenerator[dict, None]:
        """Generate a new episode with streaming."""
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            yield {"event": "error", "data": "Story not found"}
            return

        # Update story status
        if story.status == StoryStatus.DRAFT:
            story.status = StoryStatus.IN_PROGRESS
            db.commit()

        # Get episode count and create new episode
        episode_count = db.query(Episode).filter(Episode.story_id == story_id).count()
        episode_number = episode_count + 1

        new_episode = Episode(
            story_id=story_id,
            number=episode_number,
            guidance=guidance,
        )
        db.add(new_episode)
        db.commit()
        db.refresh(new_episode)

        yield {"event": "start", "data": str(new_episode.id), "episode_id": new_episode.id}

        try:
            # Get story generation settings
            story_settings = self._get_story_settings(story)

            # Determine target words: explicit param > story preset > config default
            word_preset = story_settings["target_word_preset"]
            effective_target_words = (
                target_words
                or WORD_PRESETS.get(word_preset, 1250)
                or settings.episode_target_words
            )

            # Build context with adaptive sizing based on target words
            context = await memory_service.build_context(
                db, story_id, target_words=effective_target_words
            )

            # Build prompts with style settings and structural constraints
            system_prompt = prompt_service.build_system_prompt(
                context,
                writing_style=story_settings["writing_style"],
                mood=story_settings["mood"],
                pacing=story_settings["pacing"],
            )
            user_prompt = prompt_service.build_generation_prompt(
                context,
                guidance=guidance,
                target_words=effective_target_words,
                word_preset=word_preset,
            )

            # Get the appropriate provider
            provider = ProviderManager.get_provider_for_generation(db, use_alternate)

            # Calculate max_tokens based on target word count
            max_tokens = self._calculate_max_tokens(effective_target_words)

            # Stream generation with story temperature and token limit
            full_content = ""
            current_sentence = ""
            sentence_endings = re.compile(r'[.!?]["\')\]]*\s*')

            async for token in llm_service.generate_stream(
                prompt=user_prompt,
                system_prompt=system_prompt,
                provider=provider,
                temperature=story_settings["temperature"],
                max_tokens=max_tokens,
            ):
                full_content += token
                current_sentence += token

                # Emit token event
                yield {"event": "token", "data": token, "episode_id": new_episode.id}

                # Check for sentence completion (for TTS)
                if sentence_endings.search(current_sentence):
                    sentences = sentence_endings.split(current_sentence)
                    for sentence in sentences[:-1]:
                        if sentence.strip():
                            yield {
                                "event": "sentence",
                                "data": sentence.strip(),
                                "episode_id": new_episode.id,
                            }
                    current_sentence = sentences[-1] if sentences else ""

            # Emit any remaining sentence
            if current_sentence.strip():
                yield {
                    "event": "sentence",
                    "data": current_sentence.strip(),
                    "episode_id": new_episode.id,
                }

            # Update episode with cleaned content
            new_episode.content = self._clean_content(full_content)
            new_episode.word_count = len(new_episode.content.split())

            # Generate title and summary
            title = await self._generate_title(full_content, db, use_alternate)
            summary = await memory_service.generate_summary(full_content, provider)

            new_episode.title = title
            new_episode.summary = summary

            db.commit()
            db.refresh(new_episode)

            # Save memory state
            await memory_service.save_memory_state(db, story_id, new_episode.id, context)

            yield {
                "event": "complete",
                "data": {
                    "episode_id": new_episode.id,
                    "title": title,
                    "word_count": new_episode.word_count,
                },
            }

        except Exception as e:
            yield {"event": "error", "data": str(e), "episode_id": new_episode.id}
            # Clean up failed episode
            db.delete(new_episode)
            db.commit()

    async def _generate_title(self, content: str, db: Session, use_alternate: bool = False) -> str:
        """Generate a title for the episode with fallback to alternate provider."""
        prompt = prompt_service.build_title_prompt(content)

        # Try primary provider
        provider = ProviderManager.get_provider_for_generation(db, use_alternate)
        raw = await llm_service.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=100,
            provider=provider,
        )

        title = self._clean_title(raw)

        # If empty, try the other provider as fallback
        if title == "Untitled":
            fallback_provider = ProviderManager.get_provider_for_generation(db, not use_alternate)
            if fallback_provider and fallback_provider != provider:
                raw = await llm_service.generate(
                    prompt=prompt,
                    temperature=0.7,
                    max_tokens=100,
                    provider=fallback_provider,
                )
                title = self._clean_title(raw)

        return title

    def _clean_title(self, raw: str) -> str:
        """Extract clean title from LLM response, handling preamble and multiple options."""
        # Extract first quoted string if present (handles "1. "Title" 2. "Other"")
        quoted = re.search(r'["\']([^"\']+)["\']', raw)
        if quoted:
            return quoted.group(1).strip()[:255]

        # Remove common preambles like "Here are some options:"
        cleaned = re.sub(r'^(?:Here (?:are|is)[^\n]*:?\s*)', '', raw, flags=re.IGNORECASE)
        # Remove leading numbered list format "1. "
        cleaned = re.sub(r'^\d+\.\s*', '', cleaned)
        # Final cleanup
        cleaned = cleaned.strip().strip('"\'')

        return cleaned[:255] if cleaned else "Untitled"

    # Patterns to strip from beginning of generated content
    CLEANUP_PATTERNS = [
        # Title with explanation: "Title" This title hints at...
        (r'^["\'][^"\']+["\'][\s]*(?:This title|This hints|This captures|This reflects)[^\n]*\n*', re.IGNORECASE),
        # Title suggestions intro + numbered list
        (r'^Here (?:are|is)[^\n]*(?:title|option)[^\n]*:\s*\n?(?:\d+\.[^\n]*\n)*', re.IGNORECASE),
        # Standalone numbered title lists
        (r'^(?:\d+\.\s*["\'][^\n]*\n?)+', re.MULTILINE),
        # Episode headers
        (r'^\*{0,2}Episode\s+\d+[:\s].*?\*{0,2}\s*\n+', re.IGNORECASE | re.MULTILINE),
        (r'^#{1,3}\s*Episode\s+\d+.*?\n+', re.IGNORECASE | re.MULTILINE),
        # Preamble phrases
        (r'^(?:Certainly|Sure|Of course|Absolutely)[!,.].*?\n+', re.IGNORECASE),
        (r'^(?:Here\'s|Here is)[^\n]*(?:episode|story|chapter)[^\n]*:\s*\n+', re.IGNORECASE),
    ]

    def _clean_content(self, content: str) -> str:
        """Remove common LLM meta-commentary and ensure complete ending."""
        cleaned = content

        for pattern, flags in self.CLEANUP_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=flags)

        # Strip leading/trailing whitespace
        cleaned = cleaned.strip()

        # Ensure content ends at a complete sentence/paragraph
        return self._ensure_complete_ending(cleaned)

    def _ensure_complete_ending(self, content: str) -> str:
        """Trim content to last complete sentence/paragraph if truncated.

        Two-tier approach:
        1. If last paragraph is suspiciously short, trim to previous paragraph
        2. Otherwise, trim to last complete sentence
        """
        if not content:
            return content

        content = content.rstrip()

        # Check if content already ends with sentence-ending punctuation
        if re.search(r'[.!?]["\']?$', content):
            # Content ends properly, but check for truncated final paragraph
            return self._check_paragraph_completeness(content)

        # Content doesn't end with punctuation - find last complete sentence
        matches = list(re.finditer(r'[.!?]["\']?(?=\s|$)', content))
        if matches:
            truncated = content[:matches[-1].end()].rstrip()
            # Only use truncated version if we're keeping at least 80% of content
            if len(truncated) >= len(content) * 0.8:
                return self._check_paragraph_completeness(truncated)

        return content

    def _check_paragraph_completeness(self, content: str) -> str:
        """Check if final paragraph seems complete; trim to previous if not."""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        if len(paragraphs) < 2:
            return content

        # Calculate average paragraph length (excluding last)
        other_lengths = [len(p) for p in paragraphs[:-1]]
        avg_length = sum(other_lengths) / len(other_lengths)

        # If last paragraph is less than 30% of average, it's likely truncated
        last_para_length = len(paragraphs[-1])
        if last_para_length < avg_length * 0.3:
            # Remove the truncated paragraph
            return '\n\n'.join(paragraphs[:-1]).rstrip()

        return content

    def fork_story(
        self,
        db: Session,
        story_id: int,
        from_episode: int,
        new_title: str,
    ) -> Story:
        """Fork a story from a specific episode."""
        original_story = db.query(Story).filter(Story.id == story_id).first()
        if not original_story:
            raise ValueError("Original story not found")

        # Create the forked story (copy generation settings from original)
        forked_story = Story(
            title=new_title,
            scenario_id=original_story.scenario_id,
            status=StoryStatus.IN_PROGRESS,
            parent_story_id=story_id,
            fork_from_episode=from_episode,
            # Copy generation settings
            target_word_preset=original_story.target_word_preset,
            temperature=original_story.temperature,
            writing_style=original_story.writing_style,
            mood=original_story.mood,
            pacing=original_story.pacing,
        )
        db.add(forked_story)
        db.commit()
        db.refresh(forked_story)

        # Copy characters
        for sc in original_story.story_characters:
            new_sc = StoryCharacter(
                story_id=forked_story.id,
                character_id=sc.character_id,
                role=sc.role,
            )
            db.add(new_sc)

        # Copy episodes up to fork point
        episodes_to_copy = (
            db.query(Episode)
            .filter(Episode.story_id == story_id, Episode.number <= from_episode)
            .order_by(Episode.number)
            .all()
        )

        for ep in episodes_to_copy:
            new_ep = Episode(
                story_id=forked_story.id,
                number=ep.number,
                title=ep.title,
                content=ep.content,
                summary=ep.summary,
                guidance=ep.guidance,
                word_count=ep.word_count,
            )
            db.add(new_ep)

        # Copy memory state at fork point
        fork_memory = (
            db.query(MemoryState)
            .filter(MemoryState.story_id == story_id)
            .join(Episode)
            .filter(Episode.number == from_episode)
            .first()
        )

        if fork_memory:
            # Get the last copied episode
            db.commit()  # Commit to get the new episode IDs
            last_episode = (
                db.query(Episode)
                .filter(Episode.story_id == forked_story.id)
                .order_by(Episode.number.desc())
                .first()
            )

            if last_episode:
                new_memory = MemoryState(
                    story_id=forked_story.id,
                    episode_id=last_episode.id,
                    active_memory=fork_memory.active_memory,
                    background_memory=fork_memory.background_memory,
                    faded_memory=fork_memory.faded_memory,
                    character_states=fork_memory.character_states,
                    plot_threads=fork_memory.plot_threads,
                )
                db.add(new_memory)

        db.commit()
        db.refresh(forked_story)
        return forked_story

    def get_story_tree(self, db: Session, story_id: int) -> dict:
        """Get the fork tree for a story."""
        # Find the root story
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise ValueError("Story not found")

        # Navigate to root
        root = story
        while root.parent_story_id:
            root = db.query(Story).filter(Story.id == root.parent_story_id).first()

        # Build tree recursively
        return self._build_tree_node(db, root)

    def _build_tree_node(self, db: Session, story: Story) -> dict:
        """Build a tree node for a story."""
        episode_count = db.query(Episode).filter(Episode.story_id == story.id).count()

        children = []
        for fork in story.forks:
            children.append(self._build_tree_node(db, fork))

        return {
            "id": story.id,
            "title": story.title,
            "episode_count": episode_count,
            "fork_from_episode": story.fork_from_episode,
            "children": children,
        }

    def _get_story_settings(self, story: Story) -> dict:
        """Extract generation settings from a story with defaults."""
        return {
            "target_word_preset": story.target_word_preset or "medium",
            "temperature": story.temperature if story.temperature is not None else 0.7,
            "writing_style": story.writing_style or "balanced",
            "mood": story.mood or "moderate",
            "pacing": story.pacing or "moderate",
        }

    def _calculate_max_tokens(self, target_words: int) -> int:
        """Calculate max_tokens based on target word count.

        ~1.3 tokens per word, 50% buffer to allow natural completion.
        """
        return int(target_words * 1.3 * 1.5)


# Singleton instance
story_service = StoryService()
