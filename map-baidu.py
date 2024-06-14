import requests  
import json  
  
# 百度地图API的密钥  
API_KEY = 'ndNoilvCCzpaWJcDwmh0txBao4MnpnfJ'  
  
# 要查询的地址  
ADDRESS = '北京市海淀区五道口'  
  
# 百度地图地理编码API的URL  
GEOCODING_API_URL = f'http://api.map.baidu.com/geocoding/v3/?address={ADDRESS}&output=json&ak={API_KEY}'  
print(GEOCODING_API_URL)
  
# 发送HTTP GET请求  
response = requests.get(GEOCODING_API_URL)  
  
# 检查响应状态码  
if response.status_code == 200:  
    # 解析返回的JSON数据  
    result = response.json()  
      
    # 提取结果中的经纬度信息（这里假设返回结果中只有一个地址匹配）  
    location = result['result']['location']  
    print(f"经度: {location['lng']}, 纬度: {location['lat']}")  
else:  
    print(f"请求失败，状态码: {response.status_code}")  
  
# 注意：上面的代码只是一个示例，实际使用时你可能需要处理更多的边界情况和错误
