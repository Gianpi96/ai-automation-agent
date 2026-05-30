import asyncio
import json
import logging
import time
from typing import Any

from app.config import settings
from app.models.agent import AgentResult, AgentStatus, StepLog, ToolCall
from app.services.groq_client import groq_client
from app.tools import execute_tool, get_tool_schemas

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful AI assistant that uses tools to answer questions accurately.

When given a task:
1. Think about what information you need
2. Use the available tools to gather that information
3. Analyze the results and decide if you need more information
4. Provide a clear, accurate final answer

Always use tools when you need current information or need to perform actions.
Be concise and factual in your responses."""


async def run_react_loop(query: str, context: dict | None = None) -> AgentResult:
    """
    Execute the ReAct (Reason + Act) loop:
    - Max iterations: settings.react_max_iterations (5)
    - Global timeout: settings.react_timeout (30s)
    - Per-Groq-call timeout: settings.groq_timeout (10s)
    """
    start_time = time.monotonic()
    tool_schemas = get_tool_schemas()
    tools_used: list[str] = []
    tool_calls_log: list[ToolCall] = []
    step_logs: list[StepLog] = []

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    if context:
        messages[0]["content"] += f"\n\nAdditional context: {json.dumps(context)}"

    logger.info("ReAct loop started query=%r max_iter=%d timeout=%ds",
                query, settings.react_max_iterations, settings.react_timeout)

    answer = "I was unable to complete the task within the allowed iterations."
    status = AgentStatus.COMPLETED
    iteration = 0

    try:
        async with asyncio.timeout(settings.react_timeout):
            for iteration in range(1, settings.react_max_iterations + 1):
                logger.info("ReAct iteration %d/%d", iteration, settings.react_max_iterations)
                step = StepLog(iteration=iteration)

                try:
                    response = await groq_client.chat(
                        messages=messages,
                        tools=tool_schemas,
                        tool_choice="auto",
                    )
                except asyncio.TimeoutError:
                    logger.warning("Groq call timed out at iteration %d", iteration)
                    status = AgentStatus.TIMEOUT
                    answer = "The AI service did not respond in time. Please try again."
                    break

                choice = response.choices[0]
                msg = choice.message

                # Add assistant message to history
                messages.append({"role": "assistant", "content": msg.content, "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in (msg.tool_calls or [])
                ] or None})

                # Final answer — no tool calls
                if choice.finish_reason == "stop" or not msg.tool_calls:
                    answer = msg.content or answer
                    step.thought = answer
                    step.is_final = True
                    step_logs.append(step)
                    logger.info("ReAct finished at iteration %d with final answer", iteration)
                    break

                # Process tool calls
                for tc in msg.tool_calls:
                    tool_name = tc.function.name
                    try:
                        arguments = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                    logger.info("Calling tool: %s args=%s", tool_name, arguments)
                    step.action = tool_name
                    step.action_input = arguments

                    tool_start = time.monotonic()
                    try:
                        result = await execute_tool(tool_name, arguments)
                        result_str = str(result)
                        tool_success = True
                    except Exception as e:
                        result_str = f"Tool error: {e}"
                        tool_success = False
                        logger.error("Tool %s failed: %s", tool_name, e)

                    duration_ms = int((time.monotonic() - tool_start) * 1000)
                    step.observation = result_str

                    tool_call_record = ToolCall(
                        tool_name=tool_name,
                        arguments=arguments,
                        result=result_str,
                        duration_ms=duration_ms,
                        success=tool_success,
                    )
                    tool_calls_log.append(tool_call_record)
                    if tool_name not in tools_used:
                        tools_used.append(tool_name)

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_str,
                    })

                step_logs.append(step)

                if iteration == settings.react_max_iterations:
                    logger.warning("Max iterations (%d) reached", settings.react_max_iterations)
                    # Get final answer from Groq after all tool calls
                    try:
                        final_response = await groq_client.chat(
                            messages=messages + [
                                {"role": "user", "content": "Based on all the information gathered, provide your final answer."}
                            ],
                            tools=None,
                        )
                        answer = final_response.choices[0].message.content or answer
                    except Exception:
                        pass

    except asyncio.TimeoutError:
        logger.warning("ReAct global timeout (%ds) exceeded", settings.react_timeout)
        status = AgentStatus.TIMEOUT
        answer = f"Task timed out after {settings.react_timeout} seconds."

    total_duration_ms = int((time.monotonic() - start_time) * 1000)

    confidence = _estimate_confidence(iteration, tools_used, status)

    result = AgentResult(
        answer=answer,
        tools_used=tools_used,
        iterations=iteration,
        confidence=confidence,
        status=status,
        tool_calls=tool_calls_log,
        total_duration_ms=total_duration_ms,
    )

    logger.info(
        "ReAct completed status=%s iterations=%d tools=%s confidence=%.2f duration=%dms",
        status, iteration, tools_used, confidence, total_duration_ms,
    )
    return result


def _estimate_confidence(iterations: int, tools_used: list[str], status: AgentStatus) -> float:
    if status in (AgentStatus.TIMEOUT, AgentStatus.FAILED):
        return 0.2
    base = 0.85
    if iterations == 1 and not tools_used:
        base = 0.7  # answered without tools — might be less grounded
    if iterations >= settings.react_max_iterations:
        base -= 0.1
    return round(max(0.1, min(1.0, base)), 2)
