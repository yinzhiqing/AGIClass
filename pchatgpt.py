# app.py
from flask import Flask, render_template, request, jsonify
from openai import OpenAI, ChatCompletion

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.form['message']
    # Call GPT-3 API here and get the response
    # response = call_gpt3(message)
    response = _call_gpt3(message)
    return jsonify({'message': response})

from openai import OpenAI

# 加载 .env 文件到环境变量
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

def _call_gpt3(message: str) -> str:
    # 初始化 OpenAI 服务。会自动从环境变量加载 OPENAI_API_KEY 和 OPENAI_BASE_URL
    client = OpenAI()

    # 消息
    messages = [
        {
            "role": "system",
            "content": "你是AI助手小瓜，是 AGI 课堂的助教。这门课每周二、四上课。"  # 注入新知识
        },
        {
            "role": "user",
            "content": message  # 问问题。可以改改试试
        },
    ]

    # 调用 GPT-3.5
    chat_completion = client.chat.completions.create(
        #model="gpt-3.5-turbo",
        model="gpt-4o",
        messages=messages
    )

    return chat_completion.choices[0].message.content


if __name__ == '__main__':
    app.run(debug=True)