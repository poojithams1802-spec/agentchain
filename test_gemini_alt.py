import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


models_to_test = [
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
]


for model_name in models_to_test:

    print()
    print("=" * 60)
    print("TESTING:", model_name)
    print("=" * 60)

    try:

        response = (
            client.models.generate_content(

                model=model_name,

                contents=(
                    "Reply with exactly one sentence: "
                    "What is an AI agent?"
                ),
            )
        )

        print("SUCCESS")
        print(response.text)

    except Exception as error:

        print("FAILED")
        print(
            type(error).__name__,
            str(error),
        )