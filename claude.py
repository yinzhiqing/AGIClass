
from openai import OpenAI
client = OpenAI()

chat_completion = client.chat.completions.create(
  messages=[
    {
        "role": "user", 
        "content": "你是谁， 用中文回答"
    }
  ],
  model="claude/claude-2.1",
)
print(chat_completion.choices[0].message.content) 