from google import genai
import os
from core.models import AgentState

class AnalysisAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def run(self, state: AgentState) -> AgentState:
        print("⚖️ Analysis Agent: Analyzing judgements...")
        judgements_text = ""
        for j in state.judgements:
            judgements_text += f"""
            Title: {j.title}
            Court: {j.court}
            Date: {j.date}
            Summary: {j.snippet}
            ---
            """
        prompt = f"""
        You are a senior Indian legal analyst. Analyze these judgements
        retrieved for the following case and identify key legal principles,
        reasoning patterns, and how they relate to the case.

        Original Case: {state.case_input.description}

        Retrieved Judgements:
        {judgements_text}

        Provide a structured analysis covering:
        1. Key legal principles established
        2. How courts have ruled on similar matters
        3. Most relevant precedents and why
        4. Any conflicting judgements to be aware of
        """
        response = self.client.models.generate_content(
            model="gemini-2.0-flash-lite", contents=prompt
        )
        state.analysis = response.text
        print("✅ Analysis complete")
        return state