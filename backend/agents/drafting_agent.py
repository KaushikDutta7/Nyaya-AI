from google import genai
import os
from core.models import AgentState

class DraftingAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def run(self, state: AgentState) -> AgentState:
        print("📝 Drafting Agent: Writing legal research report...")
        judgements_citations = ""
        for i, j in enumerate(state.judgements, 1):
            judgements_citations += f"{i}. {j.title} — {j.court} ({j.date})\n"
        prompt = f"""
        You are a professional legal researcher. Using all the information
        below, draft a complete, structured legal research report that a
        lawyer can directly use in court.

        Case Description: {state.case_input.description}

        Precedent Analysis:
        {state.analysis}

        Outcome Prediction:
        {state.prediction}

        Cited Judgements:
        {judgements_citations}

        Format the report with these sections:
        1. Executive Summary
        2. Legal Issues Identified
        3. Relevant Precedents & Citations
        4. Legal Analysis
        5. Predicted Outcome
        6. Recommended Arguments
        7. Conclusion
        """
        response = self.client.models.generate_content(
            model="gemini-2.0-flash-lite", contents=prompt
        )
        state.final_report = response.text
        print("✅ Report drafted successfully")
        return state