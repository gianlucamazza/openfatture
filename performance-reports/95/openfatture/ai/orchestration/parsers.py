"""Parsers for extracting tool calls from LLM text responses.

Used by ReAct orchestrator to parse tool calls from providers
that don't support native function calling (like Ollama).
"""

import json
import re
from dataclasses import dataclass
from typing import Any

from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ParsedToolCall:
    """
    Parsed tool call from LLM response.

    Attributes:
        tool_name: Name of the tool to call
        parameters: Dictionary of parameters for the tool
        thought: Optional reasoning/thought before the action
        raw_text: Original text that was parsed
    """

    tool_name: str
    parameters: dict[str, Any]
    thought: str | None = None
    raw_text: str = ""


@dataclass
class ParsedResponse:
    """
    Parsed LLM response in ReAct format.

    Attributes:
        is_final: True if this is a final answer (no more actions)
        content: Final answer content (if is_final=True)
        tool_call: Parsed tool call (if is_final=False)
        raw_text: Original response text
    """

    is_final: bool
    content: str = ""
    tool_call: ParsedToolCall | None = None
    raw_text: str = ""


class ToolCallParser:
    """
    Parser for extracting tool calls from LLM text responses.

    Modern XML-only parser (2025) - Legacy text format removed.

    Supports ReAct format:
        <thought>reasoning</thought>
        <action>tool_name</action>
        <action_input>{"param": "value"}</action_input>

    Or final answer:
        <final_answer>response</final_answer>

    Features:
    - XML-only parsing (simplified architecture)
    - Case-insensitive
    - Robust JSON parsing with auto-fix
    """

    # Regex patterns for XML tags (preferred)
    XML_THOUGHT_PATTERN = re.compile(r"<thought>(.*?)</thought>", re.IGNORECASE | re.DOTALL)
    XML_ACTION_PATTERN = re.compile(r"<action>(.*?)</action>", re.IGNORECASE | re.DOTALL)
    XML_ACTION_INPUT_PATTERN = re.compile(
        r"<action_input>(.*?)</action_input>", re.IGNORECASE | re.DOTALL
    )
    XML_FINAL_ANSWER_PATTERN = re.compile(
        r"<final_answer>(.*?)</final_answer>", re.IGNORECASE | re.DOTALL
    )

    def __init__(self) -> None:
        """Initialize parser."""
        self.parse_count = 0
        self.parse_errors = 0
        self.xml_parse_count = 0

    def parse(self, response_text: str) -> ParsedResponse:
        """
        Parse LLM response text into structured format.

        Args:
            response_text: Raw LLM response text

        Returns:
            ParsedResponse with either tool_call or final answer
        """
        self.parse_count += 1
        response_text = response_text.strip()

        logger.debug(
            "parsing_response",
            response_preview=response_text[:200],
            length=len(response_text),
        )

        # Check for final answer first
        if self._is_final_answer(response_text):
            content = self._extract_final_answer(response_text)
            return ParsedResponse(is_final=True, content=content, raw_text=response_text)

        # Try to parse as tool call
        try:
            tool_call = self._parse_tool_call(response_text)
            if tool_call:
                return ParsedResponse(is_final=False, tool_call=tool_call, raw_text=response_text)
        except Exception as e:
            logger.warning(
                "tool_call_parse_failed",
                error=str(e),
                response_preview=response_text[:200],
            )
            self.parse_errors += 1

        # If parsing failed, treat as final answer
        logger.info(
            "no_tool_call_found",
            message="Treating response as final answer",
        )
        return ParsedResponse(is_final=True, content=response_text, raw_text=response_text)

    def _is_final_answer(self, text: str) -> bool:
        """
        Check if response contains a final answer.

        Checks XML tags only (legacy format removed).

        Args:
            text: Response text

        Returns:
            True if final answer detected
        """
        return bool(self.XML_FINAL_ANSWER_PATTERN.search(text))

    def _extract_final_answer(self, text: str) -> str:
        """
        Extract final answer content from response.

        Uses XML format only (legacy format removed).

        Args:
            text: Response text

        Returns:
            Final answer content
        """
        xml_match = self.XML_FINAL_ANSWER_PATTERN.search(text)
        if xml_match:
            return xml_match.group(1).strip()

        return text.strip()

    def _parse_tool_call(self, text: str) -> ParsedToolCall | None:
        """
        Parse tool call from response text.

        XML-only parsing (legacy format removed).

        Args:
            text: Response text

        Returns:
            ParsedToolCall if XML tags found, None otherwise
        """
        xml_result = self._parse_xml_tool_call(text)
        if xml_result:
            self.xml_parse_count += 1
            logger.info(
                "tool_call_parsed_xml",
                tool_name=xml_result.tool_name,
                parameters=xml_result.parameters,
                has_thought=xml_result.thought is not None,
            )
            return xml_result

        return None

    def _parse_xml_tool_call(self, text: str) -> ParsedToolCall | None:
        """
        Parse tool call from XML tags.

        Args:
            text: Response text

        Returns:
            ParsedToolCall if XML tags found, None otherwise
        """
        # Extract action (required for tool call)
        action_match = self.XML_ACTION_PATTERN.search(text)
        if not action_match:
            return None

        tool_name = action_match.group(1).strip()

        # Extract action input (optional - default to empty dict)
        parameters = {}
        input_match = self.XML_ACTION_INPUT_PATTERN.search(text)
        if input_match:
            json_str = input_match.group(1).strip()
            try:
                parameters = json.loads(json_str)
                if not isinstance(parameters, dict):
                    logger.warning(
                        "xml_invalid_parameters_type",
                        tool_name=tool_name,
                        type=type(parameters).__name__,
                    )
                    parameters = {}
            except json.JSONDecodeError as e:
                logger.error(
                    "xml_json_parse_failed",
                    tool_name=tool_name,
                    json_str=json_str[:100],
                    error=str(e),
                )
                parameters = self._attempt_json_fix(json_str)

        # Extract thought (optional)
        thought = None
        thought_match = self.XML_THOUGHT_PATTERN.search(text)
        if thought_match:
            thought = thought_match.group(1).strip()

        return ParsedToolCall(
            tool_name=tool_name,
            parameters=parameters,
            thought=thought,
            raw_text=text,
        )

    def _attempt_json_fix(self, json_str: str) -> dict[str, Any]:
        """
        Attempt to fix common JSON formatting issues.

        Args:
            json_str: Potentially malformed JSON string

        Returns:
            Parsed dictionary or empty dict if unfixable
        """
        # Common fixes
        fixes = [
            # Single quotes to double quotes
            lambda s: s.replace("'", '"'),
            # Missing quotes around keys
            lambda s: re.sub(r"(\w+):", r'"\1":', s),
            # Trailing commas
            lambda s: s.replace(",}", "}").replace(",]", "]"),
        ]

        for fix in fixes:
            try:
                fixed = fix(json_str)
                result = json.loads(fixed)
                if isinstance(result, dict):
                    logger.info("json_fix_successful", fix_applied=fix.__name__)
                    return result
            except Exception:
                continue

        logger.warning("json_fix_failed", message="Returning empty parameters")
        return {}

    def get_stats(self) -> dict[str, Any]:
        """
        Get parser statistics.

        Returns:
            Dictionary with XML parse statistics (legacy format removed)
        """
        successful_parses = self.xml_parse_count
        return {
            "total_parses": self.parse_count,
            "parse_errors": self.parse_errors,
            "error_rate": (self.parse_errors / self.parse_count if self.parse_count > 0 else 0.0),
            "xml_parse_count": self.xml_parse_count,
            "xml_parse_rate": (
                self.xml_parse_count / successful_parses if successful_parses > 0 else 0.0
            ),
        }
