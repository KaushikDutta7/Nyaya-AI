from google import genai
import os
import json
import re
from core.models import AgentState


class QueryAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def run(self, state: AgentState) -> AgentState:
        print("Query Agent: Extracting legal keywords...")
        prompt = f"""
        You are a legal expert assistant. Given the following case description,
        extract the most relevant legal keywords, acts, and concepts that would
        help find similar judgements in Indian courts.

        Case Description: {state.case_input.description}

        Respond ONLY with a JSON object in this exact format, no extra text,
        no markdown, no backticks:
        {{
            "keywords": ["keyword1", "keyword2", "keyword3"],
            "acts": ["act1", "act2"],
            "legal_concepts": ["concept1", "concept2"]
        }}
        """
        response = self.client.models.generate_content(
            model="gemini-1.5-flash", contents=prompt
        )
        response_text = response.text.strip()

        # Strip markdown code fences if Gemini wraps in ```json ... ```
        response_text = re.sub(r"```(?:json)?\s*", "", response_text)
        response_text = re.sub(r"```", "", response_text).strip()

        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback: extract any JSON object from the response
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
            else:
                print("QueryAgent: Could not parse JSON, using fallback keywords")
                parsed = {"keywords": ["legal case", "court"], "acts": [], "legal_concepts": []}

        all_keywords = (
            parsed.get("keywords", []) +
            parsed.get("acts", []) +
            parsed.get("legal_concepts", [])
        )
        state.keywords = all_keywords
        print(f"Keywords extracted: {all_keywords}")
        return state