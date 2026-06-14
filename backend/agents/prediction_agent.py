from google import genai
import os
import json
import re
from core.models import AgentState


class PredictionAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def run(self, state: AgentState) -> AgentState:
        print("Prediction Agent: Predicting case outcome...")

        # Plain text prediction for the report
        text_prompt = f"""
        You are an experienced Indian lawyer with 20 years of experience.
        Based on the case description and legal analysis provided, predict
        the most likely outcome if this case goes to court.

        Case Description: {state.case_input.description}

        Legal Analysis of Precedents:
        {state.analysis}

        Provide:
        1. Most likely outcome (in favour of which party and why)
        2. Confidence level (High/Medium/Low) with reasoning
        3. Key factors that could change the outcome
        4. Recommended course of action
        """
        text_response = self.client.models.generate_content(
            model="gemini-1.5-flash", contents=text_prompt
        )
        state.prediction = text_response.text
        print("Prediction text complete")

        # Structured JSON prediction for the frontend UI
        json_prompt = f"""
        You are an expert Indian legal analyst.

        Case: {state.case_input.description}

        Analysis: {state.analysis}

        Respond ONLY with valid JSON, no markdown, no extra text:
        {{
            "success_rate": <integer 0-100>,
            "verdict": "<Favourable or Unfavourable>",
            "successful_arguments": ["<arg1>", "<arg2>", "<arg3>"],
            "failed_arguments": ["<arg1>", "<arg2>"],
            "risk": "<one sentence risk assessment>",
            "similar_cases": <estimated integer>,
            "won": <estimated integer cases won>
        }}
        """
        try:
            json_response = self.client.models.generate_content(
                model="gemini-1.5-flash", contents=json_prompt
            )
            raw = json_response.text.strip()
            raw = re.sub(r"```(?:json)?\s*", "", raw)
            raw = re.sub(r"```", "", raw).strip()
            state.structured_outcome = json.loads(raw)
        except Exception as e:
            print(f"Structured outcome parse failed: {e} — using defaults")
            state.structured_outcome = {
                "success_rate": 55,
                "verdict": "Uncertain",
                "successful_arguments": [
                    "Establish facts clearly with documentary evidence",
                    "Cite consistent precedents from the same court hierarchy",
                    "Demonstrate procedural compliance at every stage",
                ],
                "failed_arguments": [
                    "Relying solely on oral testimony without corroboration",
                    "Raising new grounds not pleaded in the original petition",
                ],
                "risk": "Outcome depends heavily on the quality of evidence presented.",
                "similar_cases": 50,
                "won": 28,
            }

        print("Prediction complete")
        return state