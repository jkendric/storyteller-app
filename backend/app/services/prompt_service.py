from typing import Optional


class PromptService:
    """Service for building prompts for story generation."""

    def build_system_prompt(self, context: dict) -> str:
        """Build the system prompt for story generation."""
        scenario = context["scenario"]
        characters = context["characters"]

        # Build character descriptions
        char_descriptions = []
        for char in characters:
            desc = f"- {char['name']} ({char['role']}): {char.get('description', 'No description')}"
            if char.get('personality'):
                desc += f"\n  Personality: {char['personality']}"
            if char.get('motivations'):
                desc += f"\n  Motivations: {char['motivations']}"
            char_descriptions.append(desc)

        characters_text = "\n".join(char_descriptions) if char_descriptions else "No characters defined."

        system_prompt = f"""You are a skilled fiction writer crafting an episodic story. Your task is to write engaging, immersive narrative prose.

## Story Setting
**Title**: {scenario.get('name', 'Untitled')}
**Setting**: {scenario.get('setting', 'Not specified')}
**Time Period**: {scenario.get('time_period', 'Not specified')}
**Genre**: {scenario.get('genre', 'General fiction')}
**Tone**: {scenario.get('tone', 'Neutral')}
**Premise**: {scenario.get('premise', 'Not specified')}
**Themes**: {scenario.get('themes', 'Not specified')}

## World Rules
{scenario.get('world_rules', 'Standard reality')}

## Characters
{characters_text}

## Writing Guidelines
1. Write in third person past tense
2. Show, don't tell - use vivid descriptions and actions
3. Include dialogue that reveals character
4. End episodes with hooks or cliffhangers when appropriate
5. Maintain consistency with established facts and character behaviors
6. Progress the plot while developing characters
7. Match the specified tone and genre conventions

## Important
- Stay true to character personalities and motivations
- Respect established world rules and setting details
- Build on events from previous episodes
- Create engaging narrative tension"""

        return system_prompt

    def build_generation_prompt(
        self,
        context: dict,
        guidance: Optional[str] = None,
        target_words: int = 1250,
    ) -> str:
        """Build the user prompt for episode generation."""
        episode_number = context["next_episode_number"]
        is_first_episode = episode_number == 1

        # Build memory context
        memory_parts = []

        if context.get("faded_memory"):
            memory_parts.append(f"## Story Background (Key Facts)\n{context['faded_memory']}")

        if context.get("background_memory"):
            memory_parts.append(f"## Previous Episodes (Summaries)\n{context['background_memory']}")

        if context.get("active_memory"):
            memory_parts.append(f"## Recent Episodes (Full Text)\n{context['active_memory']}")

        memory_context = "\n\n".join(memory_parts)

        # Build the prompt
        if is_first_episode:
            prompt = f"""Write the first episode of this story.

Establish the setting, introduce the main characters, and set the story in motion.
Create an engaging opening that hooks the reader and establishes the tone.

Target length: approximately {target_words} words."""

        else:
            prompt = f"""## Story Context
{memory_context}

---

Write Episode {episode_number} of this story.

Continue the narrative from where the previous episode left off.
Develop the plot and characters while maintaining consistency with established events.

Target length: approximately {target_words} words."""

        # Add user guidance if provided
        if guidance:
            prompt += f"""

## Author's Guidance for This Episode
{guidance}

Incorporate this guidance into the episode while maintaining narrative flow."""

        prompt += """

FORMAT: Start DIRECTLY with narrative prose. No preamble, no titles, no "Episode X" headers.
The first word must be story content. Begin:"""

        return prompt

    def build_summary_prompt(self, content: str) -> str:
        """Build a prompt for generating episode summaries."""
        return f"""Summarize the following story episode in 2-3 concise sentences.
Focus on: key plot developments, character actions/decisions, and important revelations.

Episode:
{content}

Summary:"""

    def build_title_prompt(self, content: str) -> str:
        """Build a prompt for generating episode titles."""
        return f"""Generate a short, evocative title for this story episode (3-6 words).
The title should hint at the episode's key event or theme without spoilers.

Episode:
{content[:1500]}...

Title:"""


# Singleton instance
prompt_service = PromptService()
