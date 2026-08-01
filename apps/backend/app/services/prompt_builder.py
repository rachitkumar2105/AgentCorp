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

        # 2. Append historical context messages
        messages.extend(history)

        # 3. Append current user instruction
        messages.append(ChatMessage(
            role=MessageRole.USER,
            content=new_user_message,
        ))

        return messages
