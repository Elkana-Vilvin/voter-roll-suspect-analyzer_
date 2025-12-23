
import re

def normalize(text):
    if not isinstance(text, str):
        return ""
    text = text.upper().strip()
    text = re.sub(r"\s+", " ", text)
    return text

def split_name(name):
    name = normalize(name)
    parts = name.split()
    if not parts:
        return "", "", True
    if len(parts) == 1:
        return parts[0], parts[0], True
    return parts[0], parts[-1], False
