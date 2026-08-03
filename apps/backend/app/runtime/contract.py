"""
Runtime contract for versioned AI execution.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable, AsyncGenerator, Any


@runtime_checkable
class RuntimeContract(Protocol):
    async def execute_chat(self, *args: Any, **kwargs: Any) -> Any:
        ...

    async def execute_stream(self, *args: Any, **kwargs: Any) -> AsyncGenerator[str, None]:
        ...

    async def execute_agent(self, *args: Any, **kwargs: Any) -> Any:
        ...

    async def execute_workflow(self, *args: Any, **kwargs: Any) -> Any:
        ...

    async def execute_tools(self, *args: Any, **kwargs: Any) -> Any:
        ...
