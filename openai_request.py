from openai import OpenAI
import user_config
client = OpenAI(api_key = user_config.openai_api)

def send_request(query):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": query
            }
        ]
    )
    return completion.choices[0].message.content