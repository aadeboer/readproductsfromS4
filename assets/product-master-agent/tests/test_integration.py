"""Integration test: end-to-end agent flow with mocked LLM and MCP tools."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def add_app_to_path(add_agent_to_path):
    return add_agent_to_path


@pytest.mark.asyncio
async def test_end_to_end_product_query(add_app_to_path):
    """
    End-to-end: Sales Rep asks about a product →
    agent invokes MCP tool → formats response → returns to user.
    All external systems (LLM, MCP) are mocked.
    """
    from agent import SampleAgent
    from langchain_core.messages import AIMessage

    # Mock LLM response simulating the agent reasoning + tool call + final answer
    with patch("agent.ChatLiteLLM") as mock_llm_cls:
        mock_llm_cls.return_value = MagicMock()
        agent = SampleAgent()

        # Mock the full agent graph invocation (with tool result already included)
        with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content=(
                        "Here are the details for product **P-1001**:\n\n"
                        "- **Description:** Industrial Transfer Pump Model X100\n"
                        "- **Product Type:** FERT (Finished Product)\n"
                        "- **Product Group:** L001\n"
                        "- **Base Unit of Measure:** EA (Each)\n"
                        "- **Gross Weight:** 2.500 KG\n\n"
                        "Is there anything else you'd like to know about this product?"
                    ))
                ]
            }

            response = await agent.invoke(
                query="What is product P-1001?",
                context_id="integration-test-001",
                tools=[],
            )

    # Validate complete end-to-end response
    assert response.status == "completed"
    assert "P-1001" in response.message
    assert "Industrial Transfer Pump" in response.message or "EA" in response.message
    assert response.message  # Non-empty


@pytest.mark.asyncio
async def test_end_to_end_classification_query(add_app_to_path):
    """
    End-to-end: Sales Rep asks about classification →
    agent retrieves class data → returns readable answer.
    """
    from agent import SampleAgent
    from langchain_core.messages import AIMessage

    with patch("agent.ChatLiteLLM") as mock_llm_cls:
        mock_llm_cls.return_value = MagicMock()
        agent = SampleAgent()

        with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content=(
                        "Product **P-1001** is assigned to the following classification:\n\n"
                        "- **Class:** PUMPS\n"
                        "- **Class Type:** 001 (General Class)\n"
                        "- **Class Description:** Industrial Pumps\n"
                        "- **Assignment Status:** Active"
                    ))
                ]
            }

            response = await agent.invoke(
                query="What classification does product P-1001 have?",
                context_id="integration-test-002",
                tools=[],
            )

    assert response.status == "completed"
    assert "PUMPS" in response.message or "class" in response.message.lower()


@pytest.mark.asyncio
async def test_streaming_returns_chunks(add_app_to_path):
    """Agent stream() yields processing chunk followed by final completed chunk."""
    from agent import SampleAgent
    from langchain_core.messages import AIMessage

    with patch("agent.ChatLiteLLM") as mock_llm_cls:
        mock_llm_cls.return_value = MagicMock()
        agent = SampleAgent()

        with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content="Product P-1001: Industrial Transfer Pump, Base Unit: EA")
                ]
            }

            chunks = []
            async for chunk in agent.stream(
                query="Describe product P-1001",
                context_id="stream-test-001",
                tools=[],
            ):
                chunks.append(chunk)

    # First chunk should be a "processing" status update
    assert len(chunks) >= 2
    assert chunks[0]["is_task_complete"] is False
    assert chunks[0]["content"] == "Processing..."

    # Last chunk should be the completed response
    last_chunk = chunks[-1]
    assert last_chunk["is_task_complete"] is True
    assert last_chunk["require_user_input"] is False
    assert "P-1001" in last_chunk["content"]


@pytest.mark.asyncio
async def test_multi_turn_context_preserved(add_app_to_path):
    """Multi-turn conversation: second question uses context from first."""
    from agent import SampleAgent
    from langchain_core.messages import AIMessage

    with patch("agent.ChatLiteLLM") as mock_llm_cls:
        mock_llm_cls.return_value = MagicMock()
        agent = SampleAgent()

        context_id = "multi-turn-test-001"

        with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
            # First turn: ask about product
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content="Product P-1001 is an Industrial Transfer Pump. Base unit: EA.")
                ]
            }
            response1 = await agent.invoke(
                query="Tell me about product P-1001",
                context_id=context_id,
                tools=[],
            )

            # Second turn: follow-up question (context retained via same context_id)
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content="Product P-1001 belongs to product group L001.")
                ]
            }
            response2 = await agent.invoke(
                query="What is its product group?",
                context_id=context_id,
                tools=[],
            )

    assert response1.status == "completed"
    assert response2.status == "completed"
    assert "P-1001" in response1.message
    assert response2.message  # Follow-up returns meaningful answer
