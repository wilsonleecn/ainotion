#!/usr/bin/env python3

import json
from datetime import datetime
from openai import OpenAI
from config_reader import Config
from extract_weekly_logs import WeeklyWorkLogExtractor

# 初始化 OpenAI 客户端
client = OpenAI(api_key=Config.AI_ENGIN_API_KEY, base_url=Config.AI_ENGIN_BASE_URL)

SYSTEM_PROMPT = """
你是一位专业的项目管理助理，请根据今天的工作记录，生成一份清晰的工作日报，内容包括：

1. 今日完成的工作：用“✅”标记；每条带有（YYYY.MM.DD）格式日期。
2. 今日未完成的工作：用“⏳”标记；每条带有（YYYY.MM.DD）格式日期，若状态为 Waiting for response，请说明是等待同事反馈。

请用中文和英文分别生成两部分内容。
"""

def generate_daily_report():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    extractor = WeeklyWorkLogExtractor(Config.NOTION_TOKEN)
    logs = extractor.get_work_logs_by_date_range(today, today)

    if not logs:
        return "❌ 今日无工作记录。"

    logs_json = json.dumps({
        "date": today.strftime("%Y-%m-%d"),
        "work_logs": logs
    }, ensure_ascii=False, indent=2)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"以下是今天的工作记录：\n{logs_json}"}
    ]
    print("----------------------------------")
    response = client.chat.completions.create(
        model="o4-mini",
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )

    return response.choices[0].message.content

def main():
    try:
        report = generate_daily_report()
        print("\n=== 今日工作日报 ===\n")
        print(report)
    except Exception as e:
        print(f"生成日报时发生错误: {str(e)}")

if __name__ == "__main__":
    main()
