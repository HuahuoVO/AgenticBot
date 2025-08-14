import json

import requests
from langchain.tools import tool

from common.constans import weather_api_key

@tool(name_or_callable="get_real_time_weather",description="获取实时天气信息")
def get_real_time_weather(location:str):
    """获取实时天气信息
    :param location: 城市名称或经纬度（如：'beijing' 或 '39.9042,116.4074'）
    :param api_key: 心知天气API密钥
    :return: 包含天气信息的字典或None
    """
    base_url = "https://api.seniverse.com/v3/weather/now.json"
    params = {
        'key': weather_api_key,
        'location': location
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # 检查HTTP请求是否成功
        result = response.json()
        # 提取关键天气信息
        if result.get('results'):
            weather_data = result['results'][0]['now']
            return json.dumps({
                'temperature': weather_data['temperature'],
                'weather': weather_data['text'],
                'wind_direction': weather_data.get('wind_direction',''),
                'wind_speed': weather_data.get('wind_speed',''),
                'update_time': result['results'][0]['last_update']
            })
        return None
    except Exception as e:
        print(f"获取天气失败: {str(e)}")
        return None

@tool(name_or_callable="get_life_index",description="获取生活指数信息")
def get_life_index(location:str):
    """获取生活指数信息
    :param location: 城市名称或经纬度（如：'beijing' 或 '39.9042,116.4074'）
    :return: 包含生活指数信息的字典或None
    """
    base_url = "https://api.seniverse.com/v3/life/suggestion.json"
    params = {
        'key': weather_api_key,
        'location': location
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # 检查HTTP请求是否成功
        result = response.json()
        # 提取关键天气信息
        if result.get('results'):
            life_index = result['results'][0]
            return json.dumps({
                'location': life_index['location'],
                'suggestions': life_index.get('suggestion', [])
            })
    except Exception as e:
        print(f"获取天气失败: {str(e)}")
        return None

if __name__ == '__main__':
    result = get_real_time_weather("北京")
    #result = get_life_index("beijing")
    print(result)
