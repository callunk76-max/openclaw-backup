import sys
import json
import os

POSITIONS_FILE = '/root/.openclaw/workspace/Trading/positions.json'

def update_position(pair, type_action):
    # Load existing
    positions = {}
    if os.path.exists(POSITIONS_FILE):
        with open(POSITIONS_FILE, 'r') as f:
            positions = json.load(f)
            
    # Normalize pair
    pair = pair.upper()
    if '/' not in pair and len(pair) == 6:
        pair = f"{pair[:3]}/{pair[3:]}"
        
    if type_action.upper() in ["BUY", "SELL"]:
        positions[pair] = {"type": type_action.upper()}
        print(f"Added/Updated: {pair} -> {type_action.upper()}")
    elif type_action.upper() == "CLOSE":
        if pair in positions:
            del positions[pair]
            print(f"Removed: {pair}")
        else:
            print(f"Pair not found: {pair}")
            
    # Save
    with open(POSITIONS_FILE, 'w') as f:
        json.dump(positions, f, indent=4)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 manage_positions.py [PAIR] [BUY|SELL|CLOSE]")
    else:
        update_position(sys.argv[1], sys.argv[2])
