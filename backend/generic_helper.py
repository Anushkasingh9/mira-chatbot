import re

def get_str_from_food_dict(food_dict: dict) -> str:
    """
    Converts a dictionary of food items and quantities to a readable string.
    Example: {'dosa': 2, 'idli': 3} → "2 dosa, 3 idli"
    """
    try:
        return ", ".join([f"{int(value)} {key}" for key, value in food_dict.items()])
    except Exception as e:
        print(f"[get_str_from_food_dict] Error: {e}")
        return ""

def extract_session_id(session_str: str) -> str:
    """
    Extracts the session ID portion from a Dialogflow session string.
    Example: projects/project-id/agent/sessions/abc123/contexts → 'abc123'
    """
    try:
        match = re.search(r"/sessions/([^/]+)", session_str)
        if match:
            return match.group(1)
        return ""
    except Exception as e:
        print(f"[extract_session_id] Error: {e}")
        return ""
