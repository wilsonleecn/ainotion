#!/usr/bin/env python3
import json
import argparse
from datetime import datetime
from openai import OpenAI
from config_reader import Config
from extract_weekly_logs import WeeklyWorkLogExtractor

# 初始化 OpenAI 客户端
client = OpenAI(api_key=Config.AI_ENGIN_API_KEY, base_url=Config.AI_ENGIN_BASE_URL)

SYSTEM_PROMPT = """
你是一位专业的项目管理助理，请根据今天的工作记录，生成一份清晰的工作日报，内容包括：

1. 今日完成的工作：用“✅”标记；每条带有（HH：MM）格式时间。
2. 按时间排序。
3. 请结合details内容给出总结后的简要细节。
4. 今日未完成的工作：用“⏳”标记；若状态为 Waiting for response，请说明是等待同事反馈。

请用中文和英文分别生成两部分内容。
"""

# def generate_daily_report():
#     today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

def generate_daily_report(for_date: datetime):
    day_start = for_date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = for_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    extractor = WeeklyWorkLogExtractor(Config.NOTION_TOKEN)
    logs = extractor.get_work_logs_by_date_range(day_start, day_end)

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
    # response = client.chat.completions.create(
    #     model="o4-mini",
    #     messages=messages,
    #     temperature=0.7,
    #     max_tokens=1000
    # )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )

    return response.choices[0].message.content

def main():
    parser = argparse.ArgumentParser(description="生成指定日期的工作日报")
    parser.add_argument("date", nargs="?", help="可选参数：指定日期 (YYYY-MM-DD)，不填默认为今天")
    args = parser.parse_args()
    
    try:
        if args.date:
            try:
                for_date = datetime.strptime(args.date, "%Y-%m-%d")
            except ValueError:
                print("❌ 输入的日期格式错误，应为 YYYY-MM-DD")
                return
        else:
            for_date = datetime.now()

        report = generate_daily_report(for_date)
        print(f"\n=== {for_date.strftime('%Y-%m-%d')} 工作日报 ===\n")
        print(report)

    except Exception as e:
        print(f"生成日报时发生错误: {str(e)}")

    # try:
    #     report = generate_daily_report()
    #     print("\n=== 今日工作日报 ===\n")
    #     print(report)
    # except Exception as e:
    #     print(f"生成日报时发生错误: {str(e)}")

if __name__ == "__main__":
    main()
