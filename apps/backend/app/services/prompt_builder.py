"""
Prompt Builder to prepare final system prompts and messages for provider invocation.
"""

from app.providers.schemas import ChatMessage, MessageRole


class PromptBuilder:
    """
    Constructs the final list of messages to send to the provider.
    Combines agent instructions, conversation history, and the new query.
    """

    def build_prompt(
        self,
        system_prompt: str,
        history: list[ChatMessage],
        new_user_message: str,
        memory_context: str | None = None,
        knowledge_context: str | None = None,
        tool_context: str | None = None,
    ) -> list[ChatMessage]:
        """
        Merge system prompt, historical messages, and current user input.
        """
        messages: list[ChatMessage] = []

        # 1. Inject Agent System instructions
        if system_prompt:
            messages.append(ChatMessage(
                role=MessageRole.SYSTEM,
                content=system_prompt,
            ))

        supplemental_context = self._format_supplemental_context(
            memory_context=memory_context,
            knowledge_context=knowledge_context,
            tool_context=tool_context,
        )
        if supplemental_context:
            messages.append(ChatMessage(
                role=MessageRole.SYSTEM,
                content=supplemental_context,
            ))

        # 2. Append historical context messages
        messages.extend(history)

        # 3. Append current user instruction
        messages.append(ChatMessage(
            role=MessageRole.USER,
            content=new_user_message,
        ))

        return messages

    def _format_supplemental_context(
        self,
        *,
        memory_context: str | None,
        knowledge_context: str | None,
        tool_context: str | None,
    ) -> str:
        sections: list[str] = []
        if memory_context:
            sections.append(f"Relevant memory:\n{memory_context}")
        if knowledge_context:
            sections.append(f"Retrieved knowledge:\n{knowledge_context}")
        if tool_context:
            sections.append(f"Available tools:\n{tool_context}")
        return "\n\n".join(sections)
