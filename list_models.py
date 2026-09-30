import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


print("=" * 70)
print("AVAILABLE GEMINI MODELS")
print("=" * 70)


for model in client.models.list():

    actions = getattr(
        model,
        "supported_actions",
        [],
    )

    if "generateContent" in actions:

        print(
            model.name,
            "|",
            getattr(
                model,
                "display_name",
                "",
            ),
        )