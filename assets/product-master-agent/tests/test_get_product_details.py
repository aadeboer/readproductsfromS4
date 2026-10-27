"""Unit tests for product detail retrieval tool interactions."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def add_app_to_path(add_agent_to_path):
    """Ensure app/ is on sys.path."""
    return add_agent_to_path


@pytest.mark.asyncio
async def test_product_detail_query_calls_tool(add_app_to_path):
    """Agent calls the product list/get tool when asked about a product."""
    from agent import SampleAgent

    mock_tool_response = json.dumps({
        "Product": "P-1001",
        "ProductType": "FERT",
        "BaseUnit": "EA",
        "ProductGroup": "L001",
    })

    mock_tool = AsyncMock()
    mock_tool.name = "get_product_for_sap_self"
    mock_tool.description = "Retrieve a single product entity by its key."
    mock_tool.arun = AsyncMock(return_value=mock_tool_response)
    mock_tool.args_schema = None

    with patch("agent.ChatLiteLLM") as mock_llm_cls:
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        agent = SampleAgent()

        with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
            from langchain_core.messages import AIMessage
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content=(
                        "**Product:** P-1001\n"
                        "**Type:** FERT\n"
                        "**Base Unit:** EA\n"
                        "**Product Group:** L001"
                    ))
                ]
            }

            response = await agent.invoke(
                query="What are the details of product P-1001?",
                context_id="test-ctx-001",
                tools=[mock_tool],
            )

    assert response.status == "completed"
    assert "P-1001" in response.message


@pytest.mark.asyncio
async def test_product_response_is_formatted(add_app_to_path):
    """Agent returns structured readable response, not raw JSON."""
    from agent import SampleAgent

    with patch("agent.ChatLiteLLM") as mock_llm_cls:
        mock_llm_cls.return_value = MagicMock()
        agent = SampleAgent()

        with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
            from langchain_core.messages import AIMessage
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content=(
                        "Here are the details for product P-1001:\n\n"
                        "**Description:** Industrial Transfer Pump Model X100\n"
                        "**Category:** L001\n"
                        "**Base Unit of Measure:** EA (Each)"
                    ))
                ]
            }

            response = await agent.invoke(
                query="Tell me about product P-1001",
                context_id="test-ctx-002",
                tools=[],
            )

    assert response.status == "completed"
    # Response should be human-readable, not raw JSON
    assert "{" not in response.message or "**" in response.message
