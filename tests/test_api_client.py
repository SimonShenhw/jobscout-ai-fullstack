"""
[ZH] api_client 单元测试 / [EN] Unit tests for api_client

Run with: pytest tests/test_api_client.py -v
"""
import sys
import os
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "frontend_ui"))

import api_client


class TestRunPipeline:
    @patch("api_client.requests.request")
    def test_successful_pipeline(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "jobs": [{"company": "Test Co", "job_title": "Engineer"}],
            "resume_tips": ["Tip 1"],
            "interview_prep": [],
            "cost_of_living": [],
            "errors": [],
        }
        mock_request.return_value = mock_response

        result = api_client.run_pipeline("Boston", "AI", 1, "")
        assert result["status"] == "success"
        assert result["is_live"] is True
        assert len(result["jobs"]) == 1

    @patch("api_client.requests.request")
    def test_connection_error_falls_back_to_mock(self, mock_request):
        import requests as _requests
        mock_request.side_effect = _requests.exceptions.ConnectionError()

        result = api_client.run_pipeline("Boston", "AI", 2, "")
        assert result["status"] == "success"
        assert result["is_live"] is False
        assert len(result["jobs"]) == 2  # mock data

    @patch("api_client.requests.request")
    def test_response_includes_cost_of_living(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "jobs": [{"company": "X"}],
            "cost_of_living": [{"affordability": "🟢 Comfortable"}],
            "resume_tips": [],
            "interview_prep": [],
            "errors": [],
        }
        mock_request.return_value = mock_response

        result = api_client.run_pipeline("Boston", "AI", 1, "")
        assert "cost_of_living" in result
        assert result["cost_of_living"][0]["affordability"] == "🟢 Comfortable"


class TestGetInterviewFeedback:
    @patch("api_client.requests.post")
    def test_successful_feedback(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "feedback": "Great answer!",
            "score": 8,
        }
        mock_post.return_value = mock_response

        result = api_client.get_interview_feedback(
            question="Tell me about yourself",
            answer="I am...",
            job_title="Engineer",
            company="Test",
        )
        assert result["status"] == "success"
        assert result["score"] == 8

    @patch("api_client.requests.post")
    def test_feedback_falls_back_on_error(self, mock_post):
        mock_post.side_effect = Exception("Connection refused")

        result = api_client.get_interview_feedback(
            question="Q?", answer="A.", job_title="", company=""
        )
        assert result["status"] == "fallback"
        assert "feedback" in result


class TestMockData:
    def test_mock_pipeline_response_has_all_fields(self):
        result = api_client._mock_pipeline_response(3)
        for key in ["status", "jobs", "resume_tips", "interview_prep", "cost_of_living", "errors"]:
            assert key in result
        assert len(result["jobs"]) == 3
        assert len(result["cost_of_living"]) == 3

    def test_mock_respects_num_results(self):
        for n in [1, 2, 3, 5]:
            result = api_client._mock_pipeline_response(n)
            assert len(result["jobs"]) == n
            assert len(result["cost_of_living"]) == n


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
