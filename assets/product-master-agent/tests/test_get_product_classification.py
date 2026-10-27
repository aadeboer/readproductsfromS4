"""Unit tests for product classification tool interactions."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def add_app_to_path(add_agent_to_path):
    return add_agent_to_path


@pytest.mark.asyncio
async def test_classification_query_returns_class_info(add_app_to_path):
    """Agent returns classification information when asked about product class."""
    from agent import SampleAgent

    mock_tool_response = json.dumps({
        "value": [
            {
                "Product": "P-1001",
                "ClassType": "001",
                "Class": "PUMPS",
                "ClassAssignmentStatus": "1",
            }
        ]
    })

    mock_tool = AsyncMock()
    mock_tool.name = "list_a_productclass_for_api_clfn_product_srv"
    mock_tool.description = "Retrieve a list of product class assignments."
    mock_tool.arun = AsyncMock(return_value=mock_tool_response)
    mock_tool.args_schema = None

    with patch("agent.ChatLiteLLM") as mock_llm_cls:
        mock_llm_cls.return_value = MagicMock()
        agent = SampleAgent()

        with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
            from langchain_core.messages import AIMessage
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content=(
                        "Product P-1001 belongs to the following classification:\n\n"
                        "**Class:** PUMPS\n"
                        "**Class Type:** 001\n"
                        "**Assignment Status:** Active (1)"
                    ))
                ]
            }

            response = await agent.invoke(
                query="What class does product P-1001 belong to?",
                context_id="test-ctx-003",
                tools=[mock_tool],
            )

    assert response.status == "completed"
    assert "PUMPS" in response.message or "class" in response.message.lower()


@pytest.mark.asyncio
async def test_no_classification_data_handled_gracefully(add_app_to_path):
    """Agent handles empty classification response gracefully."""
    from agent import SampleAgent

    with patch("agent.ChatLiteLLM") as mock_llm_cls:
        mock_llm_cls.return_value = MagicMock()
        agent = SampleAgent()

        with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
            from langchain_core.messages import AIMessage
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content=(
                        "No classification data was found for product P-9999 in SAP S/4HANA. "
                        "This product may not have any class assignments."
                    ))
                ]
            }

            response = await agent.invoke(
                query="What class does product P-9999 belong to?",
                context_id="test-ctx-004",
                tools=[],
            )

    assert response.status == "completed"
    assert response.message  # Should not be empty
    # Should not return raw empty JSON or crash
    assert response.message != "{}" and response.message != "[]"
