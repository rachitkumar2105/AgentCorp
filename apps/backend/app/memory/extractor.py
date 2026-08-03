"""
Memory Engine — Memory extractor.
"""




class MemoryExtractor:
    """
    Identifies fact candidates and preferences from dialogue histories.
    """

    def extract_memories(self, conversation_history: str) -> list[dict]:
        """
        Parses the conversation history and extracts all user preference statements.
        Returns a list of memory dicts, one per detected preference.
        """
        import re
        if not conversation_history:
            return []
        memories = []
        # Split on sentence terminators
        sentences = re.split(r"[.!?]+", conversation_history)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if re.search(r"\b(prefer|like)\b", sentence, re.IGNORECASE):
                # Ensure sentence ends with a period for consistency
                content = sentence.rstrip() + "."
                memories.append({
                    "title": "User preference",
                    "content": content,
                    "importance_score": 0.6,
                    "confidence_score": 0.8,
                    "memory_type": "semantic",
                })
        return memories
