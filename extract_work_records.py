import os
import json
from notion_client import Client
from datetime import datetime
import re
import mysql.connector

class WorkRecordExtractor:
    def __init__(self, token):
        """初始化Notion客户端"""
        self.notion = Client(auth=token)
        # 添加数据库连接配置
        self.db_config = {
            'host': 'mariadb',
            'user': 'dbuer',  # 请根据实际情况修改
            'password': 'db3213',  # 请根据实际情况修改
            'database': 'work_records'
        }
        
    def find_work_record_pages(self):
        """查找所有工作记录相关的页面"""
        work_records = []
        start_cursor = None
        
        while True:
            response = self.notion.search(
                query="工作记录",
                filter={"property": "object", "value": "page"},
                start_cursor=start_cursor,
                page_size=100
            )
            
            for page in response['results']:
                # 获取页面标题
                title = self._get_page_title(page)
                
                # 检查是否是月度工作记录（格式：工作记录YYYYMM）
                if re.match(r'工作记录\d{6}$', title):
                    work_records.append({
                        'id': page['id'],
                        'title': title,
                        'created_time': page['created_time'],
                        'last_edited_time': page['last_edited_time']
                    })
            
            if not response.get('has_more'):
                break
            start_cursor = response.get('next_cursor')
            
        return work_records

    def _get_page_title(self, page):
        """获取页面标题"""
        if 'properties' not in page:
            return "Untitled"
            
        title_props = ['Name', 'title', 'Title']
        for prop_name in title_props:
            if prop_name in page['properties']:
                title_array = page['properties'][prop_name].get('title', [])
                if title_array:
                    return title_array[0]['plain_text']
        return "Untitled"

    def find_database_in_page(self, page_id):
        """在页面中查找数据库"""
        try:
            children = self.notion.blocks.children.list(block_id=page_id)
            for block in children['results']:
                if block['type'] == 'child_database':
                    return block['id']
            return None
        except Exception as e:
            print(f"查找数据库时出错: {str(e)}")
            return None

    def extract_database_content(self, database_id):
        """提取数据库内容"""
        try:
            all_records = []
            has_more = True
            start_cursor = None
            
            while has_more:
                response = self.notion.databases.query(
                    database_id=database_id,
                    start_cursor=start_cursor,
                    page_size=100
                )
                
                for record in response['results']:
                    processed_record = self._process_record(record)
                    all_records.append(processed_record)
                
                has_more = response.get('has_more', False)
                start_cursor = response.get('next_cursor')
            
            return all_records
            
        except Exception as e:
            print(f"提取数据库内容时出错: {str(e)}")
            return []

    def _process_record(self, record):
        """处理数据库记录"""
        processed = {
            'id': record['id'],
            'created_time': record['created_time'],
            'last_edited_time': record['last_edited_time'],
            'properties': {}
        }
        
        for prop_name, prop_data in record['properties'].items():
            processed['properties'][prop_name] = self._extract_property_value(prop_data)
            
        return processed

    def _extract_property_value(self, prop_data):
        """提取属性值"""
        prop_type = prop_data['type']
        
        if prop_type == 'title':
            return self._extract_rich_text(prop_data['title'])
        elif prop_type == 'rich_text':
            return self._extract_rich_text(prop_data['rich_text'])
        elif prop_type == 'date':
            if prop_data['date']:
                return prop_data['date']['start']
            return None
        elif prop_type == 'select':
            if prop_data['select']:
                return prop_data['select']['name']
            return None
        elif prop_type == 'multi_select':
            return [item['name'] for item in prop_data['multi_select']]
        elif prop_type == 'checkbox':
            return prop_data['checkbox']
        elif prop_type == 'number':
            return prop_data['number']
        else:
            return None

    def _extract_rich_text(self, rich_text_array):
        """提取富文本内容"""
        if not rich_text_array:
            return ""
        return " ".join(text['plain_text'] for text in rich_text_array)

    def save_to_json(self, data, filename="work_records.json"):
        """保存数据到JSON文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"数据已保存到: {filename}")
        except Exception as e:
            print(f"保存JSON文件时出错: {str(e)}")

    def save_to_database(self, all_data):
        """保存数据到MySQL数据库"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            for page_title, page_data in all_data.items():
                # 从标题中提取年月 (格式：工作记录YYYYMM)
                year_month = page_title[-6:]  # 获取YYYYMM部分
                
                # 删除同年同月的记录
                cursor.execute("""
                    DELETE r, c 
                    FROM records r
                    LEFT JOIN co_workers c ON r.id = c.record_id
                    WHERE r.page_id IN (
                        SELECT id FROM pages 
                        WHERE title LIKE %s
                    )
                """, (f'%{year_month}',))
                
                cursor.execute("DELETE FROM pages WHERE title LIKE %s", (f'%{year_month}',))
                
                # 插入页面信息
                page_info = page_data['page_info']
                cursor.execute("""
                    INSERT INTO pages (id, title, created_time, last_edited_time, database_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    page_info['id'],
                    page_info['title'],
                    datetime.fromisoformat(page_info['created_time'].replace('Z', '+00:00')),
                    datetime.fromisoformat(page_info['last_edited_time'].replace('Z', '+00:00')),
                    page_data['database_id']
                ))

                # 插入记录
                for record in page_data['records']:
                    props = record['properties']
                    cursor.execute("""
                        INSERT INTO records (
                            id, page_id, created_time, last_edited_time,
                            title, type, note, timestamp, status,
                            details, request_from
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        record['id'],
                        page_info['id'],
                        datetime.fromisoformat(record['created_time'].replace('Z', '+00:00')),
                        datetime.fromisoformat(record['last_edited_time'].replace('Z', '+00:00')),
                        props.get('标题', ''),
                        props.get('类型', ''),
                        props.get('备注', ''),
                        props.get('时间'),
                        props.get('状态', ''),
                        props.get('详情', ''),
                        props.get('来源', '')
                    ))

                    # 插入协作者信息
                    co_workers = props.get('协作者', [])
                    if isinstance(co_workers, list):
                        for co_worker in co_workers:
                            cursor.execute("""
                                INSERT INTO co_workers (record_id, co_worker_name)
                                VALUES (%s, %s)
                            """, (record['id'], co_worker))

            conn.commit()
            print("数据已成功保存到数据库")

        except Exception as e:
            print(f"保存到数据库时出错: {str(e)}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

def main():
    NOTION_TOKEN = "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"
    
    extractor = WorkRecordExtractor(NOTION_TOKEN)
    
    # 查找所有工作记录页面
    print("正在查找工作记录页面...")
    work_records = extractor.find_work_record_pages()
    print(f"找到 {len(work_records)} 个工作记录页面")
    
    # 收集所有数据库内容
    all_data = {}
    for record in work_records:
        print(f"\n处理页面: {record['title']}")
        
        # 查找数据库ID
        database_id = extractor.find_database_in_page(record['id'])
        if not database_id:
            print(f"在页面 {record['title']} 中未找到数据库")
            continue
            
        # 提取数据库内容
        print(f"正在提取数据库内容...")
        database_content = extractor.extract_database_content(database_id)
        print(f"提取了 {len(database_content)} 条记录")
        
        # 存储数据
        all_data[record['title']] = {
            'page_info': record,
            'database_id': database_id,
            'records': database_content
        }
    
    # 保存所有数据
    output_filename = f"work_records_{datetime.now().strftime('%Y%m%d')}.json"
    extractor.save_to_json(all_data, output_filename)
    
    # 添加保存到数据库的步骤
    extractor.save_to_database(all_data)

if __name__ == "__main__":
    main() 