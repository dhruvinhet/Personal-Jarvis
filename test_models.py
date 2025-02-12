import openai
import user_config  # Import your API key from user_config.py

openai.api_key = user_config.openai_api

try:
    response = openai.Model.list()
    models = [model["id"] for model in response["data"]]
    print("Available Models:", models)
except Exception as e:
    print("Error:", e)
