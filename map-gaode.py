import requests  
import json  
  
# 你的高德地图API Key  
API_KEY = 'd89ce657ac77c1f267cce3874cc0f9a7'  
amap_key= API_KEY
  
# 要查询的地址  
address = '北京市朝阳区'  
  
# 构造API请求的URL  
url = f'https://restapi.amap.com/v3/geocode/geo?address={address}&key={API_KEY}'  

location="五道口"
city="北京"
url = f"https://restapi.amap.com/v5/place/text?key={amap_key}&keywords={location}&region={city}"
  
# 发送HTTP请求  
response = requests.get(url)  
  
# 检查响应状态码  
if response.status_code == 200:  
    # 解析JSON响应  
    data = response.json()  
    print(data)
    if 'status' in data and data['status'] == '1':  
        # 提取经纬度信息  
        location = data['geocodes'][0]['location']  
        print(f'经纬度：{location}')  
    else:  
        print('查询失败：', data['message'])  
else:  
    print('请求失败：', response.status_code)
