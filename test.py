import json
import re

# Original malformed string
malformed_str = '''[\n    {\n        \"fitting number\": \"KAZ-K061\",\n        \"qty\": \"2\",\n        \"part number\": \"RC04\",\n        \"description\": \"4\" (101.6) DIA. - STAINLESS STEEL CAST RING\",\n        \"duct dia\": \"4\" (101.6)\",\n        \"duct length\": \"\",\n        \"confidence score\": 100\n    },\n    {\n        \"fitting number\": \"KAZ-M013\",\n        \"qty\": \"3\",\n        \"part number\": \"RC06\",\n        \"description\": \"6\" (152.4) DIA. - STAINLESS STEEL CAST RING\",\n        \"duct dia\": \"6\" (152.4)\",\n        \"duct length\": \"\",\n        \"confidence score\": 100\n    },\n    {\n        \"fitting number\": \"KAZ-L016\",\n        \"qty\": \"6\",\n        \"part number\": \"RC08\",\n        \"description\": \"8\" (203.2) DIA. - STAINLESS STEEL CAST RING\",\n        \"duct dia\": \"8\" (203.2)\",\n        \"duct length\": \"\",\n        \"confidence score\": 100\n    },\n    {\n        \"fitting number\": \"\",\n        \"qty\": \"\",\n        \"part number\": \"RC10\",\n        \"description\": \"10\" (254.0) DIA. - STAINLESS STEEL CAST RING\",\n        \"duct dia\": \"10\" (254.0)\",\n        \"duct length\": \"\",\n        \"confidence score\": 100\n    },\n    {\n        \"fitting number\": \"\",\n        \"qty\": \"\",\n        \"part number\": \"RC12\",\n        \"description\": \"12\" (304.8) DIA. - STAINLESS STEEL CAST RING\",\n        \"duct dia\": \"12\" (304.8)\",\n        \"duct length\": \"\",\n        \"confidence score\": 100\n    },\n    {\n        \"fitting number\": \"\",\n        \"qty\": \"\",\n        \"part number\": \"RC14\",\n        \"description\": \"14\" (355.6) DIA. - STAINLESS STEEL CAST RING\",\n        \"duct dia\": \"14\" (355.6)\",\n        \"duct length\": \"\",\n        \"confidence score\": 100\n    }\n]'''

# Fix improperly escaped quotes inside values
fixed_str = re.sub(r'(\d+)"\s*\(([\d.]+)\)', r'\1\\" (\2)', malformed_str)

# Convert to JSON
try:
    json_obj = json.loads(fixed_str)
    print(json.dumps(json_obj, indent=4))
except json.JSONDecodeError as e:
    print("Failed to parse JSON:", e)
