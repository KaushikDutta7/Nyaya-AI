from dotenv import load_dotenv
from core.pipeline import NyayAIPipeline

load_dotenv()


if __name__ == "__main__":
    pipeline = NyayAIPipeline()
    report = pipeline.run(
        "A tenant has not paid rent for 6 months and the landlord wants to evict him in Mumbai"
    )
    print(report)
