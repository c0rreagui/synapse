"""
Simple Oracle Test - Runs without pytest
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_oracle_ping():
    """Test Oracle health check."""
    print("🧪 Test 1: Oracle Ping...")
    try:
        from core.oracle import oracle
        result = oracle.ping()
        
        assert "status" in result, "Missing 'status' key"
        assert "faculties" in result, "Missing 'faculties' key"
        assert result["faculties"]["mind"] == "active"
        assert result["faculties"]["sense"] == "active"
        
        print(f"   ✅ PASSED - Status: {result['status']}")
        print(f"   Engine: {result.get('engine', 'unknown')}")
        return True
    except Exception as e:
        print(f"   ❌ FAILED - {e}")
        return False


def test_oracle_is_online():
    """Test Oracle online check."""
    print("🧪 Test 2: Oracle is_online()...")
    try:
        from core.oracle import oracle
        is_online = oracle.is_online()
        assert isinstance(is_online, bool)
        print(f"   ✅ PASSED - Online: {is_online}")
        return True
    except Exception as e:
        print(f"   ❌ FAILED - {e}")
        return False


def test_json_parsing_robustness():
    """Test JSON parsing with edge cases."""
    print("🧪 Test 3: JSON Parsing Robustness...")
    import json
    import re
    
    test_cases = [
        ('```json\n{"status": "ok"}\n```', True),
        ('{"status": "ok"}', True),
        ('Text before {"status": "ok"} text after', True),
    ]
    
    passed = 0
    for test_input, should_parse in test_cases:
        clean = test_input.replace("```json", "").replace("```", "").strip()
        try:
            result = json.loads(clean)
            passed += 1
        except json.JSONDecodeError:
            # Try regex fallback
            json_match = re.search(r'\{.*\}', clean, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    passed += 1
                except:
                    if should_parse:
                        print(f"   ❌ Failed to parse: {test_input[:30]}...")
    
    total = len(test_cases)
    if passed == total:
        print(f"   ✅ PASSED - {passed}/{total} cases")
        return True
    else:
        print(f"   ⚠️ PARTIAL - {passed}/{total} cases")
        return False


def test_mind_faculty_structure():
    """Test Mind faculty exists and has correct methods."""
    print("🧪 Test 4: Mind Faculty Structure...")
    try:
        from core.oracle.faculties.mind import MindFaculty
        
        assert hasattr(MindFaculty, 'analyze_profile')
        print("   ✅ PASSED - MindFaculty has analyze_profile method")
        return True
    except Exception as e:
        print(f"   ❌ FAILED - {e}")
        return False


def test_sense_faculty_structure():
    """Test Sense faculty exists and has correct methods."""
    print("🧪 Test 5: Sense Faculty Structure...")
    try:
        from core.oracle.faculties.sense import SenseFaculty
        
        sense = SenseFaculty()
        assert hasattr(sense, 'collect_profile')
        assert hasattr(sense, 'collect_comments')
        assert hasattr(sense, 'capture_profile_screenshot')
        print("   ✅ PASSED - SenseFaculty has all required methods")
        return True
    except Exception as e:
        print(f"   ❌ FAILED - {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔮 ORACLE TEST SUITE - Simple Runner")
    print("="*60 + "\n")
    
    tests = [
        test_oracle_ping,
        test_oracle_is_online,
        test_json_parsing_robustness,
        test_mind_faculty_structure,
        test_sense_faculty_structure,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   💥 EXCEPTION - {e}")
            failed += 1
        print()
    
    print("="*60)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED")
