from agents import (
    QueryAgent,
    RetrievalAgent,
    AnalysisAgent,
    PredictionAgent,
    DraftingAgent,
    ExtractionAgent
)
from core.models import AgentState, CaseInput
import time
from dotenv import load_dotenv

load_dotenv()
 

class NyayAIPipeline:
    def __init__(self):
        self.extraction_agent = ExtractionAgent()
        self.query_agent = QueryAgent()
        self.retrieval_agent = RetrievalAgent()
        self.analysis_agent = AnalysisAgent()
        self.prediction_agent = PredictionAgent()
        self.drafting_agent = DraftingAgent()

    def _run_agent(self, agent, name, state, retries=3, **kwargs):
        for attempt in range(retries):
            try:
                print(f"⚡ Running {name}...")
                if kwargs:
                    result = agent.run(state, **kwargs)
                else:
                    result = agent.run(state)
                print(f"✅ {name} completed")
                return result
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    wait = (attempt + 1) * 30
                    print(f"⏳ {name} quota hit — waiting {wait}s before retry {attempt + 1}/{retries}...")
                    time.sleep(wait)
                elif "404" in error_msg or "NOT_FOUND" in error_msg:
                    print(f"❌ {name} model not found — check your Gemini model name")
                    raise
                else:
                    print(f"❌ {name} failed: {error_msg}")
                    if attempt == retries - 1:
                        raise
                    time.sleep(5)
        raise Exception(f"{name} failed after {retries} attempts")

    def run_from_text(self, case_description: str, court_type: str = None):
        print("\n🚀 NyayAI Pipeline Starting...\n")

        if not case_description or len(case_description.strip()) < 10:
            raise ValueError("Case description is too short. Please provide more details.")

        state = AgentState(
            case_input=CaseInput(
                description=case_description.strip(),
                court_type=court_type
            )
        )

        state = self._run_agent(self.query_agent, "Query Agent", state)
        state = self._run_agent(self.retrieval_agent, "Retrieval Agent", state)
        state = self._run_agent(self.analysis_agent, "Analysis Agent", state)
        state = self._run_agent(self.prediction_agent, "Prediction Agent", state)
        state = self._run_agent(self.drafting_agent, "Drafting Agent", state)

        print("\n✅ Pipeline Complete!\n")
        return state.final_report

    def run_from_pdf(self, pdf_path: str, court_type: str = None):
        print("\n🚀 NyayAI Pipeline Starting from PDF...\n")

        if not pdf_path or not pdf_path.endswith(".pdf"):
            raise ValueError("Invalid file. Please upload a valid PDF.")

        state = AgentState(
            case_input=CaseInput(court_type=court_type)
        )

        state = self._run_agent(
            self.extraction_agent, "Extraction Agent", state, pdf_path=pdf_path
        )
        state = self._run_agent(self.query_agent, "Query Agent", state)
        state = self._run_agent(self.retrieval_agent, "Retrieval Agent", state)
        state = self._run_agent(self.analysis_agent, "Analysis Agent", state)
        state = self._run_agent(self.prediction_agent, "Prediction Agent", state)
        state = self._run_agent(self.drafting_agent, "Drafting Agent", state)

        print("\n✅ Pipeline Complete!\n")
        return state.final_report
