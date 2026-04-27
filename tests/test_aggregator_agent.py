"""Tests for AggregatorAgent"""
import pytest
from unittest.mock import MagicMock, patch
from src.agents.aggregator_agent import AggregatorAgent
from src.models.schemas import ReviewComment


@pytest.fixture
def aggregator_agent():
    """Create aggregator agent with mocked LLM"""
    with patch("src.agents.aggregator_agent.ChatOpenAI") as mock_llm:
        mock_instance = MagicMock()
        mock_llm.return_value = mock_instance

        agent = AggregatorAgent()

        # Mock the chain to return a JSON response
        mock_response = MagicMock()
        mock_response.content = """{
            "overall_status": "success",
            "summary": "Review found 3 issues, 1 critical, mainly involving security",
            "total_issues": 3,
            "critical_issues": 1,
            "by_category": {"security": 1, "bug": 1, "style": 1}
        }"""

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = mock_response
        agent.llm = mock_instance

        # Store mock chain for later patching
        agent._mock_chain = mock_chain

        return agent


class TestAggregatorAgent:
    """Test cases for AggregatorAgent"""

    def test_aggregate_empty_results(self, aggregator_agent):
        """Test aggregation with no results"""
        with patch.object(aggregator_agent, "prompt") as mock_prompt:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = MagicMock(content="""{
                "overall_status": "success",
                "summary": "No issues found",
                "total_issues": 0
            }""")
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)

            result = aggregator_agent.aggregate({})

            assert result["overall_status"] == "success"
            assert len(result["comments"]) == 0

    def test_aggregate_single_agent_results(self, aggregator_agent):
        """Test aggregation with results from one agent"""
        agent_results = {
            "security": [
                {
                    "file": "src/auth.py",
                    "comments": [
                        {"line": 10, "severity": "critical", "message": "SQL injection vulnerability"}
                    ]
                }
            ]
        }

        with patch.object(aggregator_agent, "prompt") as mock_prompt:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = MagicMock(content="""{
                "overall_status": "success",
                "summary": "Found 1 security issue"
            }""")
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)

            result = aggregator_agent.aggregate(agent_results)

            assert len(result["comments"]) == 1
            assert result["comments"][0].file == "src/auth.py"
            assert result["comments"][0].severity == "critical"
            assert result["comments"][0].category == "security"

    def test_aggregate_multiple_agents(self, aggregator_agent):
        """Test aggregation with results from multiple agents"""
        agent_results = {
            "security": [
                {
                    "file": "src/auth.py",
                    "comments": [
                        {"line": 10, "severity": "critical", "message": "SQL injection vulnerability"}
                    ]
                }
            ],
            "bug": [
                {
                    "file": "src/utils.py",
                    "comments": [
                        {"line": 25, "severity": "error", "message": "Null pointer exception"}
                    ]
                }
            ],
            "style": [
                {
                    "file": "src/main.py",
                    "comments": [
                        {"line": 5, "severity": "info", "message": "Missing docstring"}
                    ]
                }
            ]
        }

        with patch.object(aggregator_agent, "prompt") as mock_prompt:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = MagicMock(content="""{
                "overall_status": "success",
                "summary": "Review found 3 issues, 1 critical, mainly involving security"
            }""")
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)

            result = aggregator_agent.aggregate(agent_results)

            assert len(result["comments"]) == 3

            # Verify categories are preserved
            categories = {c.category for c in result["comments"]}
            assert categories == {"security", "bug", "style"}

    def test_aggregate_preserves_severity(self, aggregator_agent):
        """Test that severity levels are preserved"""
        agent_results = {
            "bug": [
                {
                    "file": "test.py",
                    "comments": [
                        {"line": 1, "severity": "critical", "message": "Critical bug"},
                        {"line": 2, "severity": "warning", "message": "Warning"},
                        {"line": 3, "severity": "info", "message": "Info"},
                    ]
                }
            ]
        }

        with patch.object(aggregator_agent, "prompt") as mock_prompt:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = MagicMock(content="""{
                "overall_status": "success",
                "summary": "Found issues"
            }""")
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)

            result = aggregator_agent.aggregate(agent_results)

            severities = {c.severity for c in result["comments"]}
            assert severities == {"critical", "warning", "info"}

    def test_aggregate_handles_invalid_llm_response(self, aggregator_agent):
        """Test handling of invalid LLM JSON response"""
        agent_results = {
            "bug": [
                {
                    "file": "test.py",
                    "comments": [
                        {"line": 1, "severity": "error", "message": "Bug found"}
                    ]
                }
            ]
        }

        with patch.object(aggregator_agent, "prompt") as mock_prompt:
            mock_chain = MagicMock()
            # Return invalid JSON
            mock_chain.invoke.return_value = MagicMock(content="not valid json")
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)

            result = aggregator_agent.aggregate(agent_results)

            # Should fallback to default values
            assert result["overall_status"] == "success"
            assert len(result["comments"]) == 1

    def test_aggregate_returns_proper_structure(self, aggregator_agent):
        """Test that aggregate returns expected dict structure"""
        agent_results = {
            "security": [
                {"file": "a.py", "comments": [{"line": 1, "severity": "error", "message": "X"}]}
            ]
        }

        with patch.object(aggregator_agent, "prompt") as mock_prompt:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = MagicMock(content="""{
                "overall_status": "partial",
                "summary": "Some agents failed"
            }""")
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)

            result = aggregator_agent.aggregate(agent_results)

            # Check structure
            assert "overall_status" in result
            assert "summary" in result
            assert "comments" in result
            assert isinstance(result["comments"], list)
            assert all(isinstance(c, ReviewComment) for c in result["comments"])