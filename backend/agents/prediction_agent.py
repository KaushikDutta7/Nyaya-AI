from google import genai
import os
from core.models import AgentState

class PredictionAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def run(self, state: AgentState) -> AgentState:
        print("🔮 Prediction Agent: Predicting case outcome...")
        prompt = f"""
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
        response = self.client.models.generate_content(
            model="gemini-2.0-flash-lite", contents=prompt
        )
        state.prediction = response.text
        print("✅ Prediction complete")
        return state