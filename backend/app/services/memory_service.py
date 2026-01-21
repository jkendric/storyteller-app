import json
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Episode, MemoryState, Story, StoryCharacter
from app.services.llm_service import llm_service


class MemoryService:
    """Service for managing the 3-tier memory system."""

    ACTIVE_MEMORY_EPISODES = 3  # Full text for last N episodes
    BACKGROUND_MEMORY_EPISODES = 7  # Summaries for episodes 4-10 (7 more)

    async def build_context(self, db: Session, story_id: int, target_words: int = 1250) -> dict:
        """Build the full context for story generation.

        Args:
            db: Database session
            story_id: ID of the story
            target_words: Target word count for the episode (affects context sizing)
        """
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise ValueError(f"Story {story_id} not found")

        episodes = (
            db.query(Episode)
            .filter(Episode.story_id == story_id)
            .order_by(Episode.number.desc())
            .all()
        )

        # Adaptive active memory based on target length
        if target_words <= 750:
            active_episodes = 1
            use_condensed = True
        elif target_words <= 1250:
            active_episodes = 2
            use_condensed = False
        else:
            active_episodes = self.ACTIVE_MEMORY_EPISODES  # 3
            use_condensed = False

        # Build memory tiers with adaptive sizing
        active_memory = self._build_active_memory(
            episodes[:active_episodes],
            condensed=use_condensed
        )
        background_memory = self._build_background_memory(
            episodes[active_episodes:active_episodes + self.BACKGROUND_MEMORY_EPISODES]
        )
        faded_memory = await self._build_faded_memory(
            db, story_id, episodes[active_episodes + self.BACKGROUND_MEMORY_EPISODES:]
        )

        # Get character states
        character_states = self._get_character_states(db, story)

        # Get scenario context
        scenario_context = self._get_scenario_context(story)

        return {
            "scenario": scenario_context,
            "characters": character_states,
            "active_memory": active_memory,
            "background_memory": background_memory,
            "faded_memory": faded_memory,
            "episode_count": len(episodes),
            "next_episode_number": len(episodes) + 1,
        }

    def _build_active_memory(self, episodes: list[Episode], condensed: bool = False) -> str:
        """Build active memory from recent episodes.

        Args:
            episodes: List of recent episodes
            condensed: If True, use summary + last paragraphs only (reduces context ~80%)
        """
        if not episodes:
            return ""

        parts = []
        for ep in reversed(episodes):  # Chronological order
            if condensed:
                # Condensed format: summary + last 2 paragraphs only
                content_parts = []
                if ep.summary:
                    content_parts.append(f"Summary: {ep.summary}")
                ending = self._get_last_paragraphs(ep.content, n=2)
                if ending:
                    content_parts.append(f"Ending:\n{ending}")
                content = "\n\n".join(content_parts)
            else:
                # Full format: entire episode text
                content = ep.content

            parts.append(f"=== Episode {ep.number}: {ep.title or 'Untitled'} ===\n{content}")

        return "\n\n".join(parts)

    def _get_last_paragraphs(self, content: str, n: int = 2) -> str:
        """Extract the last N paragraphs from content."""
        if not content:
            return ""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        return '\n\n'.join(paragraphs[-n:]) if paragraphs else content

    def _build_background_memory(self, episodes: list[Episode]) -> str:
        """Build background memory from summaries."""
        if not episodes:
            return ""

        parts = []
        for ep in reversed(episodes):  # Chronological order
            if ep.summary:
                parts.append(f"Episode {ep.number}: {ep.summary}")

        return "\n".join(parts) if parts else ""

    async def _build_faded_memory(
        self, db: Session, story_id: int, episodes: list[Episode]
    ) -> str:
        """Build faded memory from oldest episodes (high-level facts only)."""
        if not episodes:
            return ""

        # Check if we have stored faded memory
        latest_memory = (
            db.query(MemoryState)
            .filter(MemoryState.story_id == story_id)
            .order_by(MemoryState.episode_id.desc())
            .first()
        )

        if latest_memory and latest_memory.faded_memory:
            return latest_memory.faded_memory

        # If no stored faded memory, extract key facts from summaries
        facts = []
        for ep in reversed(episodes):
            if ep.summary:
                facts.append(f"- {ep.summary}")

        return "\n".join(facts) if facts else ""

    def _get_character_states(self, db: Session, story: Story) -> list[dict]:
        """Get current state of all characters in the story."""
        characters = []
        for sc in story.story_characters:
            char = sc.character
            characters.append({
                "name": char.name,
                "role": sc.role.value,
                "description": char.description,
                "personality": char.personality,
                "motivations": char.motivations,
                "backstory": char.backstory,
            })
        return characters

    def _get_scenario_context(self, story: Story) -> dict:
        """Get scenario context for the story."""
        scenario = story.scenario
        return {
            "name": scenario.name,
            "setting": scenario.setting,
            "time_period": scenario.time_period,
            "genre": scenario.genre,
            "tone": scenario.tone,
            "premise": scenario.premise,
            "themes": scenario.themes,
            "world_rules": scenario.world_rules,
        }

    async def generate_summary(self, content: str, provider=None) -> str:
        """Generate a summary for an episode using LLM."""
        prompt = f"""Summarize the following story episode in 2-3 sentences.
Focus on key plot points, character developments, and important events.

Episode content:
{content}

Summary:"""

        summary = await llm_service.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=200,
            provider=provider,
        )
        return summary.strip()

    async def save_memory_state(
        self,
        db: Session,
        story_id: int,
        episode_id: int,
        context: dict,
    ) -> MemoryState:
        """Save the memory state after generating an episode."""
        memory_state = MemoryState(
            story_id=story_id,
            episode_id=episode_id,
            active_memory=context.get("active_memory", ""),
            background_memory=context.get("background_memory", ""),
            faded_memory=context.get("faded_memory", ""),
            character_states=json.dumps(context.get("characters", [])),
            plot_threads=json.dumps(context.get("plot_threads", [])),
        )
        db.add(memory_state)
        db.commit()
        db.refresh(memory_state)
        return memory_state


# Singleton instance
memory_service = MemoryService()
