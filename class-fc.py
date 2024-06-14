

# 初始化
import sqlite3
import copy
import json
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

client = OpenAI()


def print_json(data):
    """
    打印参数。如果参数是有结构的（如字典或列表），则以格式化的 JSON 形式打印；
    否则，直接打印该值。
    """
    if hasattr(data, 'model_dump_json'):
        data = json.loads(data.model_dump_json())

    if isinstance(data, (list)):
        for item in data:
            print_json(item)
    elif (isinstance(data, (dict))):
        print(json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        ))
    else:
        print(data)


def get_sql_completion(msg, model="gpt-3.5-turbo"):
    """
    根据用户需求获取SQL查询结果
    """
    response = client.chat.completions.create(
        model=model,
        messages=msg,
        temperature=0,
        # 摘自 OpenAI 官方示例 https://github.com/openai/openai-cookbook/blob/main/examples/How_to_call_functions_with_chat_models.ipynb
        tools=[{
            "type": "function",
            "function": {
                "name": "ask_database",
                "description": "Use this function to answer user questions about business. \
                            Output should be a fully formed SQL query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": f"""
                            SQL query extracting info to answer the user's question.
                            SQL should be written using this database schema:
                            {DATABASE_SCHEMA}
                            The query should be returned in plain text, not in JSON.
                            The query should only contain grammars supported by SQLite.
                            """,
                        }
                    },
                    "required": ["query"],
                }
            }
        }],
    )
    return response.choices[0].message


#  描述数据库表结构
DATABASE_SCHEMA = """
CREATE TABLE orders (
    id INT PRIMARY KEY NOT NULL,    -- 主键，不允许为空
    product_id INT NOT NULL,        -- 产品ID，不允许为空
    name TEXT NOT NULL,             -- 产品名称，不允许为空
    price DECIMAL(10,2) NOT NULL,   -- 价格(单位：人民币)，不允许为空
    data INT NOT NULL,              -- 流量(单位: GB)，不允许为空, 0表示不限量，大于0表示套餐最大流量值
    requirement TEXT                -- 必备条件，允许为空, 空字符串表示无要求, 非空字符串表示必须满足此要求
);
"""

'''
数据库初始化操作
'''

# 创建数据库连接
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# 创建orders表
cursor.execute(DATABASE_SCHEMA)

# 插入5条明确的模拟记录
mock_data = [
    (1, 1001, '经济套餐', 50, 10, ''),
    (2, 1002, '畅游套餐', 180, 100, ''),
    (3, 1003, '无限套餐', 300, 1000, ''),
    (4, 1004, '校园套餐', 150, 200, '在校生')
]

for record in mock_data:
    cursor.execute('''
    INSERT INTO orders (id, product_id, name, price, data, requirement)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', record)

# 提交事务
conn.commit()


def ask_database(query):
    cursor.execute(query)
    records = cursor.fetchall()
    return records


messages = [
    {
      "role": "system",
      "content": """你是一个手机流量套餐的客服代码，你叫小清，基于数据库的数据帮助客户选择最合适的流量套餐产品。
       介绍套餐时候依照下面的格式：
       如果有合适套餐:
          用户说：300太贵了，200元以内有吗?
          回答： 经济套餐，月费50元，流量10GB，无要求
       如果没有合适套餐:
          用户说：300太贵了，200元以内有吗?
          回答：抱歉，没有合适的套餐
      """
    },
    {
        "role": "user",
        "content": "都有哪些套餐？"
    }
]

INFO_LEVEL = 0 # 0: 不输出信息，1: 输出信息

def output(*args):
    """
    输出查询结果
    """
    for arg in args:
      if INFO_LEVEL == 1:
         print(arg)


def run(prompt_user):
    """
    运行函数, 通过用户输入的问题, 获取客服的回答
    """
    messages.append({
        "role": "user",
        "content": prompt_user
        })

    response = get_sql_completion(messages, model="gpt-4o")
    if response.content is None:
        response.content = ""
    new_messages = copy.deepcopy(messages)
    new_messages.append(response)
    output("====Function Calling====", response)
    if response.tool_calls is not None:
        tool_call = response.tool_calls[0]
        if tool_call.function.name == "ask_database":
            arguments = tool_call.function.arguments
            args = json.loads(arguments)
            output("====SQL====", args["query"])
            result = ask_database(args["query"])
            output("====DB Records====", result)
            new_messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": "ask_database",
                "content": str(result)
            })
            response = get_sql_completion(new_messages)
            messages.append(response)
            print(response.content)


run("都有哪些套餐？")

prompt = input("请输入您的套餐需求(退出请输入：exit)：")
while prompt != "exit":
    run(prompt)
    prompt = input("请输入您的套餐需求(退出请输入：exit)：")
