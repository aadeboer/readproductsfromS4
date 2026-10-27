"""Unit tests for out-of-scope question handling (pricing, availability, orders)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def add_app_to_path(add_agent_to_path):
    return add_agent_to_path


@pytest.mark.asyncio
async def test_pricing_question_handled_gracefully(add_app_to_path):
    """Agent does not attempt tool calls for pricing questions and explains the limitation."""
    from agent import SampleAgent

    with patch("agent.ChatLiteLLM") as mock_llm_cls:
        mock_llm_cls.return_value = MagicMock()
        agent = SampleAgent()

        with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
            from langchain_core.messages import AIMessage
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content=(
                        "I'm sorry, but pricing information is not available through this assistant. "
                        "Please check pricing directly in SAP or contact your pricing team for "
                        "accurate price information for product P-1001."
                    ))
                ]
            }

            response = await agent.invoke(
                query="What is the price of product P-1001?",
                context_id="test-ctx-005",
                tools=[],
            )

    assert response.status == "completed"
    assert response.message  # Should not be empty
    # Should explain the limitation, not return an error
    assert "error" not in response.message.lower() or "not available" in response.message.lower()


@pytest.mark.asyncio
async def test_availability_question_handled_gracefully(add_app_to_path):
    """Agent does not attempt tool calls for stock availability questions."""
    from agent import SampleAgent

    with patch("agent.ChatLiteLLM") as mock_llm_cls:
        mock_llm_cls.return_value = MagicMock()
        agent = SampleAgent()

        with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
            from langchain_core.messages import AIMessage
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content=(
                        "Stock availability information is not available through this assistant. "
                        "Please check stock levels directly in SAP or contact your logistics team."
                    ))
                ]
            }

            response = await agent.invoke(
                query="Is product P-1001 in stock?",
                context_id="test-ctx-006",
                tools=[],
            )

    assert response.status == "completed"
    assert response.message
    assert "not available" in response.message.lower() or "sap" in response.message.lower()


@pytest.mark.asyncio
async def test_order_creation_rejected(add_app_to_path):
    """Agent declines order creation requests."""
    from agent import SampleAgent

    with patch("agent.ChatLiteLLM") as mock_llm_cls:
        mock_llm_cls.return_value = MagicMock()
        agent = SampleAgent()

        with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
            from langchain_core.messages import AIMessage
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content=(
                        "I'm not able to create orders. This assistant is designed to answer "
                        "questions about product master data only. For order creation, please use "
                        "the order management system in SAP."
                    ))
                ]
            }

            response = await agent.invoke(
                query="Create an order for 10 units of product P-1001",
                context_id="test-ctx-007",
                tools=[],
            )

    assert response.status == "completed"
    assert response.message
    assert "not able" in response.message.lower() or "cannot" in response.message.lower() or "sap" in response.message.lower()
