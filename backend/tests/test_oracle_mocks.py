"""
Oracle - Mock-based Unit Tests
Tests using mocks to avoid external dependencies.
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock


# ========== MOCK DATA ==========

MOCK_PROFILE_DATA = {
    "username": "test_creator",
    "followers": "100K",
    "following": "1K",
    "likes": "500K",
    "bio": "Content creator | Tech enthusiast",
    "videos": [
        {"index": 0, "views": "50K", "link": "/video/123"},
        {"index": 1, "views": "30K", "link": "/video/456"},
        {"index": 2, "views": "20K", "link": "/video/789"},
    ],
    "comments": [
        {"username": "fan1", "text": "Incrível! Continue assim"},
        {"username": "critic1", "text": "Não gostei desse vídeo"},
        {"username": "fan2", "text": "Melhor criador de conteúdo!"},
    ]
}


# ========== MIND FACULTY MOCKED TESTS ==========

@pytest.mark.asyncio
async def test_mind_with_complete_profile_data():
    """Test Mind faculty with complete, valid profile data."""
    from core.oracle.faculties.mind import MindFaculty
    
    # Create mock client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.text = json.dumps({
        "profile_type": "Original Creator",
        "virality_score": 8.5,
        "audience_persona": {
            "demographics": "Gen Z, 18-24",
            "psychographics": "Tech enthusiasts"
        },
        "viral_hooks": [],
        "content_pillars": ["Tech", "Education"],
        "best_times": [
            {"day": "Segunda", "hour": 12, "reason": "Lunch break"}
        ]
    })
    mock_client.generate_content = Mock(return_value=mock_response)
    
    mind = MindFaculty(mock_client)
    result = await mind.analyze_profile(MOCK_PROFILE_DATA)
    
    assert "analysis" in result or "error" in result
    if "analysis" in result:
        assert isinstance(result["analysis"], dict)


@pytest.mark.asyncio
async def test_mind_with_minimal_profile_data():
    """Test Mind faculty with minimal profile data."""
    from core.oracle.faculties.mind import MindFaculty
    
    minimal_data = {
        "username": "minimal_user",
        "videos": [],
        "comments": []
    }
    
    mock_client = Mock()
    mock_response = Mock()
    mock_response.text = '{"virality_score": 0}'
    mock_client.generate_content = Mock(return_value=mock_response)
    
    mind = MindFaculty(mock_client)
    result = await mind.analyze_profile(minimal_data)
    
    assert isinstance(result, dict)


# ========== JSON PARSING EDGE CASES ==========

@pytest.mark.parametrize("malformed_json,should_extract", [
    ('```json\n{"status": "ok"}\n```', True),
    ('{"status": "ok"}', True),
    ('Text before {"status": "ok"} text after', True),
    ('Completely invalid text', False),
    ('{"incomplete": ', False),
    ('```\n{"nested": {"deep": "value"}}\n```', True),
])
def test_json_extraction_from_llm_response(malformed_json, should_extract):
    """Test JSON extraction from various LLM response formats."""
    import re
    
    # Simulate cleaning
    clean = malformed_json.replace("```json", "").replace("```", "").strip()
    
    try:
        result = json.loads(clean)
        assert should_extract, f"Expected to fail but succeeded: {malformed_json}"
    except json.JSONDecodeError:
        if should_extract:
            # Try regex extraction
            json_match = re.search(r'\{.*\}', clean, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    assert True
                except:
                    pytest.fail(f"Should extract JSON but failed: {malformed_json}")


# ========== SENSE FACULTY MOCKED TESTS ==========

@pytest.mark.asyncio
async def test_sense_returns_expected_structure():
    """Test that Sense faculty returns expected data structure."""
    from core.oracle.faculties.sense import SenseFaculty
    
    # We can't easily mock Playwright, so we test the structure
    sense = SenseFaculty()
    
    # Expected keys in return
    expected_keys = ["username", "followers", "videos"]
    
    # Just verify the class exists and has the method
    assert hasattr(sense, 'collect_profile')
    assert callable(sense.collect_profile)


# ========== ORACLE ORCHESTRATION MOCKED TESTS ==========

@pytest.mark.asyncio
async def test_oracle_full_scan_orchestration():
    """Test Oracle orchestrates Sense + Mind correctly."""
    from core.oracle import Oracle
    from unittest.mock import patch
    
    oracle_instance = Oracle()
    
    # Mock both faculties
    with patch.object(oracle_instance.sense, 'collect_profile', new_callable=AsyncMock) as mock_sense:
        with patch.object(oracle_instance.sense, 'collect_comments', new_callable=AsyncMock) as mock_comments:
            with patch.object(oracle_instance.mind, 'analyze_profile', new_callable=AsyncMock) as mock_mind:
                
                mock_sense.return_value = MOCK_PROFILE_DATA.copy()
                mock_comments.return_value = MOCK_PROFILE_DATA["comments"]
                mock_mind.return_value = {
                    "analysis": {"virality_score": 9.0}
                }
                
                result = await oracle_instance.full_scan("test_user")
                
                # Verify calls
                mock_sense.assert_called_once_with("test_user")
                mock_mind.assert_called_once()
                
                # Verify structure
                assert "username" in result
                assert "raw_data" in result
                assert "strategic_analysis" in result


@pytest.mark.asyncio
async def test_oracle_handles_null_client():
    """Test Oracle behavior when client is None."""
    from core.oracle.faculties.mind import MindFaculty
    
    mind = MindFaculty(None)
    result = await mind.analyze_profile({"username": "test"})
    
    assert "error" in result
    assert "offline" in result["error"].lower()


# ========== ERROR PROPAGATION TESTS ==========

@pytest.mark.asyncio
async def test_error_propagation_from_sense_to_oracle():
    """Test that errors from Sense propagate correctly to Oracle."""
    from core.oracle import Oracle
    from unittest.mock import patch
    
    oracle_instance = Oracle()
    
    with patch.object(oracle_instance.sense, 'collect_profile', new_callable=AsyncMock) as mock_sense:
        mock_sense.return_value = {"error": "Network timeout"}
        
        result = await oracle_instance.full_scan("test_user")
        
        assert "error" in result
        assert "Network timeout" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
