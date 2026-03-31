AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。

# 可用工具:
- `get_weather(city: str)`: 查询指定城市的实时天气。
- `get_attraction(city: str, weather: str)`: 根据城市和天气搜索推荐的旅游景点。

# 输出格式要求:
你的每次回复必须严格遵循以下格式，包含一对Thought和Action：

Thought: [你的思考过程和下一步计划]
Action: [你要执行的具体行动]

Action的格式必须是以下之一：
1. 调用工具：function_name(arg_name="arg_value")
2. 结束任务：Finish[最终答案]

# 重要提示:
- 每次只输出一对Thought-Action
- Action必须在同一行，不要换行
- 当收集到足够信息可以回答用户问题时，必须使用 Action: Finish[最终答案] 格式结束

请开始吧！
"""

# 工具1：查询真是天气
import requests

def get_weather(city: str) -> str:
    url = f"https://wttr.in/{city}?format=j1"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        current_condition = data['current_condition'][0]
        wether_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']
        
        return f"{city}当前的天气是{wether_desc}，温度是{temp_c}摄氏度"
    except requests.RequestException as e:
        return f"查询{city}天气时遇到网络问题：{str(e)}"
    except (KeyboardInterrupt,IndexError) as e:
        return f"错误：解析天气数据失败，可能是城市名称无效 - {e}"
    
# 工具2：搜索并推荐旅游景点
import os
from tavily import TavilyClient

def get_attraction(city: str, weather: str) -> str:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "错误：未配置TAVILY_API_KEY环境变量"
    
    travily = TavilyClient(api_key=api_key)
    query = f"'{city}'在'{weather}'天气下最值得去的旅游景点推荐及理由"
    
    try:
        response = travily.search(query=query, search_depth="basic", include_answer=True)
        if response.get("answer"):
            return response["answer"]
        formatted_results = []
        for result in response["results"]:
            formatted_results.append(f"-{result['title']}：{result['content']}")

        if not formatted_results:
            return f"抱歉，没有找到相关的旅游景点"
        return "根据搜索，为您找到以下信息:\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"错误：执行Tavily搜索时出现问题：{str(e)}"

# 将所有工具函数放入一个字典带你，供主循环调用
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction
}

# 接入大语言模型
from openai import OpenAI

class OpenAICompatibleClient:

    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        print("正在调用大语言模型")
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            answer = response.choices[0].message.content
            print("大语言模型响应成功")
            return answer
        except Exception as e:
            print(f"调用大语言模型时出现问题：{str(e)}")
            return f"错误：调用大语言模型时出现问题：{str(e)}"
   
# 组合所有组件，执行行动循坏
API_KEY = 'sk-oBqyVXQe4aCnz5487293A9B63c9146E2A23c9a328e293855'
BASE_URL = 'https://aihubmix.com/v1'
MODEL = 'coding-glm-4.7-free'
