"""Data models for AI tools and function calling."""

from collections.abc import Callable
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from openfatture.platform.errors import describe_error


class ToolParameterType(StrEnum):
    """Parameter type for tools."""

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ToolRisk(StrEnum):
    """What a tool can affect. The agent access policy decides by this class.

    - ``read``: only reads local data.
    - ``lookup``: reads a public registry over the network (fixed endpoint,
      validated identifier sent, nothing changed); off with ``ai_offline``.
    - ``local_artifact``: writes or opens a document inside the exports or
      archive directory and touches no record (PDF, XML, CSV export).
    - ``mutate``: creates, changes or deletes records.
    - ``transmit``: sends data outside the machine (SDI/PEC).
    """

    READ = "read"
    LOOKUP = "lookup"
    LOCAL_ARTIFACT = "local_artifact"
    MUTATE = "mutate"
    TRANSMIT = "transmit"


class ToolParameter(BaseModel):
    """
    A parameter for a tool function.

    Follows OpenAI Function Calling schema format.
    """

    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    enum: list[str] | None = None
    default: Any | None = None
    items: dict[str, Any] | None = None  # For array types

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function parameter schema."""
        schema: dict[str, Any] = {
            "type": self.type.value,
            "description": self.description,
        }

        if self.enum:
            schema["enum"] = self.enum

        if self.items:
            schema["items"] = self.items

        return schema


class Tool(BaseModel):
    """
    A callable tool/function that the AI can use.

    Wraps a Python function with metadata for function calling.
    Follows OpenAI Function Calling format.
    """

    # Metadata
    name: str = Field(..., description="Unique tool name (snake_case)")
    description: str = Field(..., description="What the tool does")
    category: str = Field(default="general", description="Tool category")

    # Parameters
    parameters: list[ToolParameter] = Field(default_factory=list)

    # Implementation
    func: Callable = Field(..., description="Python function to execute")

    # Control
    risk: ToolRisk = Field(
        default=ToolRisk.MUTATE,
        description="Risk class; unclassified tools are treated as mutating (fail-closed)",
    )
    requires_confirmation: bool = Field(
        default=False,
        description="Ask user confirmation before executing",
    )
    enabled: bool = Field(default=True, description="Tool is enabled")
    retry_safe: bool = Field(
        default=False, description="Explicitly safe to retry transient read failures"
    )

    # Metadata
    examples: list[str] = Field(default_factory=list, description="Usage examples")
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_openai_function(self) -> dict[str, Any]:
        """
        Convert to OpenAI function calling format.

        Returns:
            Dictionary in OpenAI function schema format
        """
        # Build parameters schema
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_openai_schema()
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def to_anthropic_tool(self) -> dict[str, Any]:
        """
        Convert to Anthropic tool calling format.

        Returns:
            Dictionary in Anthropic tool schema format
        """
        # Build input schema
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_openai_schema()  # Same format
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    async def execute(self, **kwargs: Any) -> "ToolResult":
        """
        Execute the tool with given parameters.

        Args:
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution outcome
        """
        import asyncio
        import time

        from openfatture.platform.rate_limiter import ExponentialBackoff

        start_time = time.time()

        try:
            # Validate parameters (basic check)
            for param in self.parameters:
                if param.required and param.name not in kwargs:
                    execution_time = time.time() - start_time
                    return ToolResult(
                        success=False,
                        error=f"Required parameter '{param.name}' missing",
                        tool_name=self.name,
                        execution_time=execution_time,
                    )

            # Execute function with retry logic
            backoff = ExponentialBackoff(base=0.5, max_delay=5.0)
            max_retries = 3 if self.retry_safe else 1

            for attempt in range(max_retries):
                try:
                    # Check if async
                    import inspect

                    if inspect.iscoroutinefunction(self.func):
                        result = await self.func(**kwargs)
                    else:
                        result = self.func(**kwargs)

                    execution_time = time.time() - start_time
                    if isinstance(result, dict) and result.get("error"):
                        # Application services report refusals as {"error": ...}:
                        # a failed call, not an infrastructure fault.
                        return ToolResult(
                            success=False,
                            data=result,
                            error=str(result["error"]),
                            error_type=str(result.get("error_code") or "application_error"),
                            metadata={"application_error": True},
                            tool_name=self.name,
                            execution_time=execution_time,
                            retries=attempt,
                        )
                    return ToolResult(
                        success=True,
                        data=result,
                        tool_name=self.name,
                        execution_time=execution_time,
                        retries=attempt,
                    )

                except Exception as e:
                    error_type = type(e).__name__

                    # Check if this is a retryable error
                    retryable_errors = (
                        ConnectionError,
                        TimeoutError,
                    )

                    if attempt < max_retries - 1 and isinstance(e, retryable_errors):
                        delay = backoff.get_delay(attempt)
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # Final failure
                        execution_time = time.time() - start_time
                        return ToolResult(
                            success=False,
                            error=describe_error(e),
                            error_type=error_type,
                            metadata={"outcome_uncertain": not self.retry_safe},
                            tool_name=self.name,
                            execution_time=execution_time,
                            retries=attempt,
                        )

        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult(
                success=False,
                error=describe_error(e),
                error_type=type(e).__name__,
                tool_name=self.name,
                execution_time=execution_time,
            )

        # This should never be reached, but mypy requires it
        return ToolResult(
            success=False,
            error="Unexpected execution path",
            tool_name=self.name,
        )


class ToolResult(BaseModel):
    """Result of tool execution."""

    success: bool
    data: Any = None
    error: str | None = None
    error_type: str | None = None
    tool_name: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Execution metadata (Phase 2 enhancements)
    execution_time: float | None = None  # Seconds
    retries: int = 0  # Number of retry attempts
    cache_hit: bool = False  # Whether result came from cache
    cache_key: str | None = None  # Cache key used (if cached)

    # Resilience metadata (Phase 3 enhancements)
    circuit_breaker_state: str | None = None  # "closed", "open", "half_open"
    bulkhead_queue_length: int | None = None  # Number of waiting requests in bulkhead queue

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "error_type": self.error_type,
            "tool_name": self.tool_name,
            "metadata": self.metadata,
            "execution_time": self.execution_time,
            "retries": self.retries,
            "cache_hit": self.cache_hit,
            "cache_key": self.cache_key,
            "circuit_breaker_state": self.circuit_breaker_state,
            "bulkhead_queue_length": self.bulkhead_queue_length,
        }

    def to_string(self) -> str:
        """Convert to human-readable string."""
        if self.success:
            return f"{self.tool_name}: {self.data}"
        else:
            return f"{self.tool_name}: {self.error}"
