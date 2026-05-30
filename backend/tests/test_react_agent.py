"""
Tests for the ReAct agent loop.
Requires GROQ_API_KEY to be set for integration tests.
Unit tests mock the Groq client.
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.agent import AgentStatus


def _make_groq_response(content: str = None, tool_calls: list = None, finish_reason: str = "stop"):
    """Build a mock Groq API response."""
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls or []

    choice = MagicMock()
    choice.message = msg
    choice.finish_reason = finish_reason

    response = MagicMock()
    response.choices = [choice]
    return response


def _make_tool_call(name: str, args: dict, call_id: str = "call_1"):
    tc = MagicMock()
    tc.id = call_id
    tc.function.name = name
    tc.function.arguments = json.dumps(args)
    return tc


@pytest.mark.asyncio
async def test_react_direct_answer():
    """Agent answers without tools when Groq returns stop immediately."""
    from app.agents.react_agent import run_react_loop

    direct_response = _make_groq_response(content="Paris is the capital of France.")

    with patch("app.agents.react_agent.groq_client") as mock_client:
        mock_client.chat = AsyncMock(return_value=direct_response)
        result = await run_react_loop("What is the capital of France?")

    assert result.answer == "Paris is the capital of France."
    assert result.iterations == 1
    assert result.tools_used == []
    assert result.status == AgentStatus.COMPLETED
    assert 0.0 <= result.confidence <= 1.0


@pytest.mark.asyncio
async def test_react_two_consecutive_tools():
    """Agent calls search_web then send_notification in two iterations."""
    from app.agents.react_agent import run_react_loop

    tool_call_1 = _make_tool_call("search_web", {"query": "Python news"}, "call_1")
    tool_call_2 = _make_tool_call("send_notification", {"message": "Found Python news"}, "call_2")

    response_with_search = _make_groq_response(tool_calls=[tool_call_1], finish_reason="tool_calls")
    response_with_notify = _make_groq_response(tool_calls=[tool_call_2], finish_reason="tool_calls")
    final_response = _make_groq_response(content="I searched for Python news and sent you a notification.")

    call_count = 0

    async def mock_chat(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return response_with_search
        elif call_count == 2:
            return response_with_notify
        return final_response

    with patch("app.agents.react_agent.groq_client") as mock_client:
        mock_client.chat = mock_chat
        result = await run_react_loop("Search for Python news and notify me")

    assert "search_web" in result.tools_used
    assert "send_notification" in result.tools_used
    assert result.iterations >= 2
    assert result.status == AgentStatus.COMPLETED


@pytest.mark.asyncio
async def test_react_max_iterations_respected():
    """Agent stops after max_iterations even if Groq keeps calling tools."""
    from app.agents.react_agent import run_react_loop
    from app.config import settings

    always_tool = _make_groq_response(
        tool_calls=[_make_tool_call("search_web", {"query": "loop"}, "call_x")],
        finish_reason="tool_calls",
    )
    final = _make_groq_response(content="Final answer after max iterations.")

    call_count = 0

    async def mock_chat(**kwargs):
        nonlocal call_count
        call_count += 1
        if kwargs.get("tools") is None:
            return final
        return always_tool

    with patch("app.agents.react_agent.groq_client") as mock_client:
        mock_client.chat = mock_chat
        result = await run_react_loop("Keep searching forever")

    assert result.iterations <= settings.react_max_iterations


@pytest.mark.asyncio
async def test_react_timeout():
    """Agent returns TIMEOUT status when Groq is slow."""
    from app.agents.react_agent import run_react_loop

    async def slow_chat(**kwargs):
        await asyncio.sleep(100)
        return _make_groq_response(content="Too late")

    with patch("app.agents.react_agent.groq_client") as mock_client:
        mock_client.chat = slow_chat
        with patch("app.config.settings.react_timeout", 1):
            with patch("app.config.settings.groq_timeout", 1):
                result = await run_react_loop("Slow query")

    assert result.status == AgentStatus.TIMEOUT


@pytest.mark.asyncio
async def test_agent_api_endpoint(client):
    """Test the /api/agent/run endpoint via HTTP."""
    direct_response = _make_groq_response(content="42 is the answer.")

    with patch("app.agents.react_agent.groq_client") as mock_client:
        mock_client.chat = AsyncMock(return_value=direct_response)
        response = await client.post("/api/agent/run", json={"query": "What is the answer?"})

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "42 is the answer."
    assert "tools_used" in data
    assert "iterations" in data
    assert "confidence" in data


@pytest.mark.asyncio
async def test_list_tools_endpoint(client):
    """Test the tools listing endpoint."""
    response = await client.get("/api/agent/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert "search_web" in data["tools"]
    assert "read_file" in data["tools"]
    assert "send_notification" in data["tools"]
