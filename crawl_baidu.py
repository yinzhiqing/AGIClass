import requests
from bs4 import BeautifulSoup

def crawl_baidu():
    print("开始爬取百度搜索结果...")
    # 百度搜索URL
    url = "https://www.baidu.com/s?wd=大模型"

    # 发送GET请求
    response = requests.get(url)

    print("请求状态码：", response.status_code)

    
    # 如果请求成功
    if response.status_code == 200:
        # 解析HTML文档
        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取所有的搜索结果
        results = soup.find_all('div', class_='c-abstract')
        print("搜索结果数量：", len(results))


        # 打印每个搜索结果的文本
        for result in results:
            print(result.get_text())

    print("爬取结束！")

# 调用函数
crawl_baidu()