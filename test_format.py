import os

PROMPT_TEMPLATE = """You are a legal AI assistant.

Analyze the contract clause.

Return ONLY JSON:

{{
"risk_level": "...",
"risk_type": "...",
"rewrite": "...",
"reason": "..."
}}

Clause:
{clause}"""

def test_format():
    clause = "Test clause content"
    try:
        prompt = PROMPT_TEMPLATE.format(clause=clause)
        print("Success! Prompt formatted correctly.")
        print("--- PROMPT START ---")
        print(prompt)
        print("--- PROMPT END ---")
    except KeyError as e:
        print(f"FAILED with KeyError: {e}")

if __name__ == "__main__":
    test_format()
