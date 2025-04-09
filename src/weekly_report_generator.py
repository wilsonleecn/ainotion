#!/usr/bin/env python3

import json
from openai import OpenAI
from config_reader import Config
from extract_weekly_logs import WeeklyWorkLogExtractor

# Initialize the OpenAI client
client = OpenAI(api_key=Config.OPENAI_API_KEY)

SYSTEM_PROMPT = """
你是一位专业的项目管理助理，请根据提供的工作记录，帮助生成一份简明的工作周报。要求：
1. 总结本周完成的重要事项。
2. 总结尚未完成的工作，若其状态为Waiting for response，则说明正在等待co-worker的后续工作。
3. 文末给出接下来工作重点和行动计划。

请用中文回复，确保内容清晰易读。
"""

def generate_weekly_report() -> str:
    """
    生成工作周报
    1. 获取一周工作日志
    2. 调用OpenAI接口生成周报
    3. 返回生成的周报内容
    """
    # 初始化工作日志提取器
    extractor = WeeklyWorkLogExtractor(Config.NOTION_TOKEN)
    
    # 获取最近一周的日期范围
    start_date, end_date = extractor.get_latest_complete_week()
    
    # 获取工作日志
    weekly_logs = extractor.get_work_logs_by_date_range(start_date, end_date)
    
    # 将工作日志转换为JSON字符串
    logs_json = json.dumps(weekly_logs, ensure_ascii=False, indent=2)
    
    # 准备消息
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"以下是我的工作记录：\n{logs_json}"}
    ]

    # 调用OpenAI接口
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )

    # 提取生成的周报内容
    weekly_report = response.choices[0].message.content
    return weekly_report

def main():
    try:
        # 生成周报
        report = generate_weekly_report()
        
        # 打印结果
        print("\n=== 本周工作周报 ===\n")
        print(report)
        
    except Exception as e:
        print(f"生成周报时发生错误: {str(e)}")

if __name__ == "__main__":
    main() 