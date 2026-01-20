import re
from typing import AsyncGenerator, Optional
from sqlalchemy.orm import Session

from app.models import Story, Episode, StoryCharacter, MemoryState
from app.models.story import StoryStatus
from app.services.llm_service import llm_service, ProviderManager
from app.services.memory_service import memory_service
from app.services.prompt_service import prompt_service
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
            # Build context
            context = await memory_service.build_context(db, story_id)

            # Build prompts
            system_prompt = prompt_service.build_system_prompt(context)
            user_prompt = prompt_service.build_generation_prompt(
                context,
                guidance=guidance,
                target_words=target_words or settings.episode_target_words,
            )

            # Get the appropriate provider
            provider = ProviderManager.get_provider_for_generation(db, use_alternate)

            # Stream generation
            full_content = ""
            current_sentence = ""
            sentence_endings = re.compile(r'[.!?]["\')\]]*\s*')

            async for token in llm_service.generate_stream(
                prompt=user_prompt,
                system_prompt=system_prompt,
                provider=provider,
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

            # Update episode with content
            new_episode.content = full_content
            new_episode.word_count = len(full_content.split())

            # Generate title and summary
            title = await self._generate_title(full_content)
            summary = await memory_service.generate_summary(full_content)

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

    async def _generate_title(self, content: str) -> str:
        """Generate a title for the episode."""
        prompt = prompt_service.build_title_prompt(content)
        title = await llm_service.generate(prompt=prompt, temperature=0.7, max_tokens=20)
        # Clean up the title
        title = title.strip().strip('"\'')
        return title[:255] if title else "Untitled"

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

        # Create the forked story
        forked_story = Story(
            title=new_title,
            scenario_id=original_story.scenario_id,
            status=StoryStatus.IN_PROGRESS,
            parent_story_id=story_id,
            fork_from_episode=from_episode,
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


# Singleton instance
story_service = StoryService()
