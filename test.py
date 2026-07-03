from google import genai
from config import GEMINI_API_KEY


def show_models():
    client = genai.Client(api_key=GEMINI_API_KEY)

    for model in client.models.list():
        print(model.name)


if __name__ == "__main__":
    show_models()