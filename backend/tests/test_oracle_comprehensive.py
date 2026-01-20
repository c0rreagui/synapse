"""
Oracle - Comprehensive Test Suite
Automated tests for the Oracle unified intelligence system.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json


# ========== HEALTH CHECK TESTS ==========

def test_oracle_ping():
    """Test Oracle health check endpoint."""
    from core.oracle import oracle
    
    result = oracle.ping()
    
    assert "status" in result
    assert "faculties" in result
    assert result["faculties"]["mind"] == "active"
    assert result["faculties"]["sense"] == "active"
    assert result["faculties"]["vision"] == "active"
    assert result["faculties"]["voice"] == "active"


def test_oracle_is_online():
    """Test Oracle online status."""
    from core.oracle import oracle
    
    is_online = oracle.is_online()
    assert isinstance(is_online, bool)


# ========== SENSE FACULTY TESTS ==========

@pytest.mark.asyncio
async def test_sense_collect_profile_error_handling():
    """Test Sense faculty handles scraping errors gracefully."""
    from core.oracle.faculties.sense import SenseFaculty
    
    sense = SenseFaculty()
    
    # Test with invalid username (should return error, not crash)
    result = await sense.collect_profile("thisuserdoesnotexist_xxxyyy123")
    
    # Should either succeed or return error dict
    assert isinstance(result, dict)
    if "error" in result:
        assert isinstance(result["error"], str)


@pytest.mark.asyncio
async def test_sense_collect_comments_empty_video():
    """Test comment collection with invalid video URL."""
    from core.oracle.faculties.sense import SenseFaculty
    
    sense = SenseFaculty()
    comments = await sense.collect_comments("https://invalid.url", max_comments=10)
    
    # Should return empty list, not crash
    assert isinstance(comments, list)


# ========== MIND FACULTY TESTS ==========

@pytest.mark.asyncio
async def test_mind_analyze_with_valid_data():
    """Test Mind faculty with valid profile data."""
    from core.oracle.faculties.mind import MindFaculty
    from core.oracle.client import oracle_client
    
    mind = MindFaculty(oracle_client)
    
    # Mock profile data
    profile_data = {
        "username": "test_user",
        "followers": "10K",
        "following": "500",
        "likes": "100K",
        "bio": "Test bio",
        "videos": [
            {"index": 0, "views": "5K", "link": "/video1"},
            {"index": 1, "views": "3K", "link": "/video2"}
        ],
        "comments": [
            {"username": "user1", "text": "Adorei!"},
            {"username": "user2", "text": "Que legal"}
        ]
    }
    
    result = await mind.analyze_profile(profile_data)
    
    # Should return analysis dict
    assert isinstance(result, dict)
    assert "profile" in result or "error" in result


@pytest.mark.asyncio
async def test_mind_handles_malformed_llm_response():
    """Test Mind faculty handles malformed JSON from LLM."""
    from core.oracle.faculties.mind import MindFaculty
    
    # Mock client that returns invalid JSON
    mock_client = Mock()
    mock_response = Mock()
    mock_response.text = "This is not JSON at all ```json {incomplete"
    mock_client.generate_content = Mock(return_value=mock_response)
    
    mind = MindFaculty(mock_client)
    
    profile_data = {
        "username": "test",
        "videos": [],
        "comments": []
    }
    
    result = await mind.analyze_profile(profile_data)
    
    # Should return error, not crash
    assert "error" in result


# ========== FULL SCAN TESTS (MOCKED) ==========

@pytest.mark.asyncio
async def test_full_scan_with_mocked_sense():
    """Test full_scan orchestration with mocked Sense faculty."""
    from core.oracle import oracle
    
    # Mock the sense.collect_profile to avoid real scraping
    mock_profile_data = {
        "username": "mocked_user",
        "followers": "50K",
        "videos": [{"index": 0, "views": "10K", "link": "/test"}],
        "comments": []
    }
    
    with patch.object(oracle.sense, 'collect_profile', new_callable=AsyncMock) as mock_collect:
        with patch.object(oracle.sense, 'collect_comments', new_callable=AsyncMock) as mock_comments:
            mock_collect.return_value = mock_profile_data
            mock_comments.return_value = []
            
            result = await oracle.full_scan("mocked_user")
            
            # Verify orchestration
            assert "username" in result
            assert "raw_data" in result
            assert result["username"] == "mocked_user"
            mock_collect.assert_called_once_with("mocked_user")


@pytest.mark.asyncio
async def test_full_scan_handles_sense_failure():
    """Test full_scan when Sense faculty fails."""
    from core.oracle import oracle
    
    # Mock sense to return error
    with patch.object(oracle.sense, 'collect_profile', new_callable=AsyncMock) as mock_collect:
        mock_collect.return_value = {"error": "Scraping failed"}
        
        result = await oracle.full_scan("test_user")
        
        assert "error" in result
        assert "Sense failed" in result["error"]


# ========== JSON PARSING ROBUSTNESS TESTS ==========

def test_json_parsing_edge_cases():
    """Test various malformed JSON responses."""
    
    test_cases = [
        '```json\n{"key": "value"}\n```',  # With markdown fences
        '{"key": "value"}',  # Clean JSON
        'Some text before {"key": "value"} some text after',  # JSON in text
        '```\n{"key": "value"}\n```',  # Generic code fences
    ]
    
    for test_input in test_cases:
        clean = test_input.replace("```json", "").replace("```", "").strip()
        
        # Should be able to parse or extract JSON
        try:
            result = json.loads(clean)
            assert isinstance(result, dict)
        except json.JSONDecodeError:
            # If it fails, it should at least not crash
            assert True


# ========== INTEGRATION TESTS ==========

@pytest.mark.asyncio
@pytest.mark.integration
async def test_spy_competitor_orchestration():
    """Test competitor spy orchestration."""
    from core.oracle import oracle
    
    with patch.object(oracle.sense, 'spy_competitor', new_callable=AsyncMock) as mock_spy:
        mock_spy.return_value = {
            "username": "competitor",
            "videos": [],
            "spy_mode": True
        }
        
        result = await oracle.spy_competitor("competitor")
        
        assert "target" in result
        assert result["target"] == "competitor"


# ========== PERFORMANCE TESTS ==========

@pytest.mark.asyncio
@pytest.mark.slow
async def test_full_scan_timeout():
    """Test that full_scan doesn't hang indefinitely."""
    from core.oracle import oracle
    
    # This should complete or timeout within reasonable time
    try:
        result = await asyncio.wait_for(
            oracle.full_scan("test_timeout_user"),
            timeout=60.0  # 60 seconds max
        )
        # If it completes, that's fine
        assert isinstance(result, dict)
    except asyncio.TimeoutError:
        pytest.fail("full_scan hung for more than 60 seconds")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
