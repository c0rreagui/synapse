
import json
import os
import sys

# Define path to state file - using hardcoded path based on previous finding
STATE_FILE = r"d:\APPS - ANTIGRAVITY\Synapse\backend\data\circuit_breaker_state.json"

def force_reset():
    print(f"Force resetting Circuit Breaker state at: {STATE_FILE}")
    
    new_state = {
        "state": "CLOSED",
        "failure_count": 0,
        "last_failure_time": 0.0
    }
    
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(new_state, f, indent=2)
        print("SUCCESS: State reset to CLOSED.")
    except Exception as e:
        print(f"ERROR: Failed to reset state: {e}")
        sys.exit(1)

if __name__ == "__main__":
    force_reset()
