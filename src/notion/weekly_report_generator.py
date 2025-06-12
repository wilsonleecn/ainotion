#!/usr/bin/env python3

import json
from openai import OpenAI
from config_reader import Config
from extract_weekly_logs import WeeklyWorkLogExtractor

# Initialize the OpenAI client
client = OpenAI(api_key=Config.AI_ENGIN_API_KEY, base_url=Config.AI_ENGIN_BASE_URL)

SYSTEM_PROMPT = """
你是一位专业的项目管理助理，请根据提供的工作记录，帮助生成一份简明的工作周报。要求：
1. 在开头标注本周报的日期范围。
2. 总结本周完成的重要事项，每一条需要用两位数字编号（如：01、02），并包含（YYYY.MM.DD）格式的日期标志。
3. 总结尚未完成的工作，每一条需要用两位数字编号（如：01、02），并包含（YYYY.MM.DD）格式的日期标志。若其状态为Waiting for response，则说明正在等待co-worker的后续工作。
4. 文末给出接下来工作重点和行动计划。

格式示例：
本周完成工作：
01.（2024.03.25）完成了XXX项目的部署
02.（2024.03.26）与XXX团队讨论了YYY方案

待完成工作：
01.（2024.03.27）等待XXX团队的反馈
02.（2024.03.28）继续推进ZZZ项目

回复请确保内容清晰易读，用中文和英文各自输出一份
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
    print(f"\n获取工作日志范围: {start_date} 到 {end_date}")
    
    # 获取工作日志
    weekly_logs = extractor.get_work_logs_by_date_range(start_date, end_date)
    
    # 检查工作日志是否为空
    if weekly_logs is None:
        return "工作日志获取失败，返回值为None。请检查数据库连接和查询条件。"
    elif not weekly_logs:
        return "未找到指定日期范围内的工作日志。请检查数据库中是否存在相应记录。"
    
    # 将工作日志转换为JSON字符串，并添加日期范围信息
    try:
        report_data = {
            "date_range": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            },
            "work_logs": weekly_logs
        }
        logs_json = json.dumps(report_data, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"转换工作日志时发生错误: {str(e)}"
    
    # 准备消息
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"以下是我的工作记录：\n{logs_json}"}
    ]

    # 调用OpenAI接口
    response = client.chat.completions.create(
        model="gpt-4o",
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