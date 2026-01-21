from typing import Optional


# Word count presets mapping
WORD_PRESETS = {
    "short": 750,
    "medium": 1250,
    "long": 2000,
    "epic": 3000,
}

# Style instruction mappings
STYLE_INSTRUCTIONS = {
    "descriptive": "Use rich, detailed descriptions of settings, characters, and sensory details. Paint vivid scenes.",
    "action": "Focus on dynamic action sequences, physical movement, and tension. Keep descriptions tight and punchy.",
    "dialogue": "Emphasize character conversations and verbal exchanges. Let personality shine through speech.",
    "balanced": "Balance description, action, and dialogue naturally based on scene needs.",
}

MOOD_INSTRUCTIONS = {
    "light": "Maintain a light, optimistic tone. Even conflicts should feel manageable.",
    "moderate": "Balance lighter and heavier moments naturally.",
    "intense": "Heighten emotional stakes. Characters feel things deeply.",
    "dark": "Embrace darker themes and emotions. Allow for tragedy and moral complexity.",
}

PACING_INSTRUCTIONS = {
    "slow": "Take time with scenes. Allow moments to breathe. Detailed internal reflection.",
    "moderate": "Natural pacing that varies with scene needs.",
    "fast": "Keep momentum high. Quick scene transitions. Punchy prose.",
}

# Structural constraints for length enforcement
LENGTH_STRUCTURES = {
    "short": {
        "word_target": 750,
        "scenes": "1-2",
        "paragraphs": "8-12",
        "instruction": "Write a focused, single-scene episode. Keep descriptions tight.",
    },
    "medium": {
        "word_target": 1250,
        "scenes": "2-3",
        "paragraphs": "15-20",
        "instruction": "Write 2-3 connected scenes. Balance action with brief reflection.",
    },
    "long": {
        "word_target": 2000,
        "scenes": "3-4",
        "paragraphs": "25-30",
        "instruction": "Develop 3-4 scenes with detailed description and dialogue.",
    },
    "epic": {
        "word_target": 3000,
        "scenes": "4-6",
        "paragraphs": "35-45",
        "instruction": "Create an expansive episode with multiple scenes and world-building.",
    },
}


class PromptService:
    """Service for building prompts for story generation."""

    def build_system_prompt(
        self,
        context: dict,
        writing_style: Optional[str] = None,
        mood: Optional[str] = None,
        pacing: Optional[str] = None,
    ) -> str:
        """Build the system prompt for story generation.

        Args:
            context: Story context including scenario and characters
            writing_style: Writing style setting (descriptive, action, dialogue, balanced)
            mood: Mood setting (light, moderate, intense, dark)
            pacing: Pacing setting (slow, moderate, fast)
        """
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

## Variation Guidelines
8. Vary sentence structures - mix short punchy sentences with longer flowing ones
9. Use fresh metaphors and descriptions - avoid repeating imagery from previous episodes
10. Find new ways to describe recurring elements (settings, character traits, emotions)"""

        # Add style configuration if any non-default settings are provided
        style_section = self._build_style_section(writing_style, mood, pacing)
        if style_section:
            system_prompt += f"\n\n{style_section}"

        system_prompt += """

## Important
- Stay true to character personalities and motivations
- Respect established world rules and setting details
- Build on events from previous episodes
- Create engaging narrative tension"""

        return system_prompt

    def _build_style_section(
        self,
        writing_style: Optional[str] = None,
        mood: Optional[str] = None,
        pacing: Optional[str] = None,
    ) -> str:
        """Build the style configuration section for the prompt."""
        parts = []

        # Only include non-default settings
        if writing_style and writing_style != "balanced":
            instruction = STYLE_INSTRUCTIONS.get(writing_style, "")
            if instruction:
                parts.append(f"**Writing Style**: {instruction}")

        if mood and mood != "moderate":
            instruction = MOOD_INSTRUCTIONS.get(mood, "")
            if instruction:
                parts.append(f"**Mood**: {instruction}")

        if pacing and pacing != "moderate":
            instruction = PACING_INSTRUCTIONS.get(pacing, "")
            if instruction:
                parts.append(f"**Pacing**: {instruction}")

        if parts:
            return "## Story Style Configuration\n\n" + "\n".join(parts)
        return ""

    def build_generation_prompt(
        self,
        context: dict,
        guidance: Optional[str] = None,
        target_words: int = 1250,
        word_preset: str = "medium",
    ) -> str:
        """Build the user prompt for episode generation."""
        episode_number = context["next_episode_number"]
        is_first_episode = episode_number == 1

        # Get structural constraints for this length preset
        structure = LENGTH_STRUCTURES.get(word_preset, LENGTH_STRUCTURES["medium"])
        max_words = int(target_words * 1.2)

        # Build length requirements section
        length_requirements = f"""## Length Requirements (CRITICAL)
- Target: approximately {target_words} words ({word_preset} episode)
- Structure: {structure['scenes']} scenes, {structure['paragraphs']} paragraphs
- {structure['instruction']}
- STOP when you reach a natural conclusion near the target length
- Do NOT exceed {max_words} words"""

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

{length_requirements}"""

        else:
            prompt = f"""## Story Context
{memory_context}

---

Write Episode {episode_number} of this story.

Continue the narrative from where the previous episode left off.
Develop the plot and characters while maintaining consistency with established events.

{length_requirements}"""

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
