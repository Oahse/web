from openai import OpenAI
client = OpenAI(api_key="sk-abcdef1234567890abcdef1234567890abcdef12")

response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message["content"])
