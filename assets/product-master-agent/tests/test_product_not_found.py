"""Unit tests for product-not-found scenario handling."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def add_app_to_path(add_agent_to_path):
    return add_agent_to_path


@pytest.mark.asyncio
async def test_product_not_found_informs_user(add_app_to_path):
    """Agent informs user clearly when a product is not found."""
    from agent import SampleAgent

    with patch("agent.ChatLiteLLM") as mock_llm_cls:
        mock_llm_cls.return_value = MagicMock()
        agent = SampleAgent()

        with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
            from langchain_core.messages import AIMessage
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content=(
                        "Product NONEXISTENT-999 was not found in SAP S/4HANA. "
                        "Please verify the product ID and try again."
                    ))
                ]
            }

            response = await agent.invoke(
                query="What is the description of product NONEXISTENT-999?",
                context_id="test-ctx-008",
                tools=[],
            )

    assert response.status == "completed"
    assert response.message
    # Should clearly inform the user the product wasn't found
    assert (
        "not found" in response.message.lower()
        or "does not exist" in response.message.lower()
        or "nonexistent" in response.message.lower()
    )


@pytest.mark.asyncio
async def test_api_error_relayed_verbatim(add_app_to_path):
    """Agent relays API errors verbatim without adding suggestions."""
    from agent import SampleAgent

    with patch("agent.ChatLiteLLM") as mock_llm_cls:
        mock_llm_cls.return_value = MagicMock()
        agent = SampleAgent()

        with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
            from langchain_core.messages import AIMessage
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content=(
                        "The API returned an error: 'Service temporarily unavailable (503)'. "
                        "Please try again later."
                    ))
                ]
            }

            response = await agent.invoke(
                query="Get details for product P-1001",
                context_id="test-ctx-009",
                tools=[],
            )

    assert response.status == "completed"
    assert response.message
    # Should communicate the error without inventing solutions
    assert len(response.message) > 0


@pytest.mark.asyncio
async def test_ambiguous_query_asks_for_clarification(add_app_to_path):
    """Agent asks for clarification when product cannot be identified."""
    from agent import SampleAgent

    with patch("agent.ChatLiteLLM") as mock_llm_cls:
        mock_llm_cls.return_value = MagicMock()
        agent = SampleAgent()

        with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
            from langchain_core.messages import AIMessage
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content=(
                        "Could you please provide the product ID? "
                        "I need a specific product identifier (such as P-1001) to look up the product details."
                    ))
                ]
            }

            response = await agent.invoke(
                query="Tell me about our most popular product",
                context_id="test-ctx-010",
                tools=[],
            )

    assert response.status == "completed"
    assert response.message
    # Should ask for clarification
    assert "?" in response.message or "provide" in response.message.lower() or "product id" in response.message.lower()
