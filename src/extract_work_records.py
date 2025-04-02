import os
import json
from notion_client import Client
from datetime import datetime
import re
import mysql.connector

class WorkRecordExtractor:
    def __init__(self, token):
        """Initialize Notion client and database configuration"""
        self.notion = Client(auth=token)
        # Add database connection configuration
        self.db_config = {
            'host': 'mariadb',
            'user': 'dbuser',  # Please modify according to actual situation
            'password': 'db3213',  # Please modify according to actual situation
            'database': 'work_records'
        }
        
    def find_work_record_pages(self):
        """Find all work record related pages"""
        work_records = []
        start_cursor = None
        
        while True:
            response = self.notion.search(
                query="工作记录",  # Search for "Work Record" in Chinese
                filter={"property": "object", "value": "page"},
                start_cursor=start_cursor,
                page_size=100
            )
            
            for page in response['results']:
                # Get page title
                title = self._get_page_title(page)
                
                # Check if it's a monthly work record (format: 工作记录YYYYMM)
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
        """Get page title"""
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
        """Find database in page"""
        try:
            children = self.notion.blocks.children.list(block_id=page_id)
            for block in children['results']:
                if block['type'] == 'child_database':
                    return block['id']
            return None
        except Exception as e:
            print(f"Error finding database: {str(e)}")
            return None

    def extract_database_content(self, database_id):
        """Extract database content"""
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
            print(f"Error extracting database content: {str(e)}")
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
        """Save data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Data saved to: {filename}")
        except Exception as e:
            print(f"Error saving JSON file: {str(e)}")

    def save_to_database(self, all_data):
        """Save data to MySQL database"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            for page_title, page_data in all_data.items():
                # Extract year and month from title (format: 工作记录YYYYMM)
                year_month = page_title[-6:]  # Get YYYYMM part
                
                # Delete records from the same year and month
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
                
                # Insert page information
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

                # Insert records
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
                        props.get('Title', ''),
                        ','.join(props.get('Type', [])),
                        props.get('Note', ''),
                        props.get('timestamp'),
                        props.get('Status', ''),
                        props.get('Details', ''),
                        props.get('Request from', '')
                    ))

                    # Insert co-worker information
                    co_workers = props.get('Co-worker', [])
                    if isinstance(co_workers, list):
                        for co_worker in co_workers:
                            cursor.execute("""
                                INSERT INTO co_workers (record_id, co_worker_name)
                                VALUES (%s, %s)
                            """, (record['id'], co_worker))

            conn.commit()
            print("Data successfully saved to database")

        except Exception as e:
            print(f"Error saving to database: {str(e)}")
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
    
    # Find all work record pages
    print("Finding work record pages...")
    work_records = extractor.find_work_record_pages()
    print(f"Found {len(work_records)} work record pages")
    
    # Collect all database content
    all_data = {}
    for record in work_records:
        print(f"\nProcessing page: {record['title']}")
        
        # Find database ID
        database_id = extractor.find_database_in_page(record['id'])
        if not database_id:
            print(f"No database found in page {record['title']}")
            continue
            
        # Extract database content
        print(f"Extracting database content...")
        database_content = extractor.extract_database_content(database_id)
        print(f"Extracted {len(database_content)} records")
        
        # Store data
        all_data[record['title']] = {
            'page_info': record,
            'database_id': database_id,
            'records': database_content
        }
    
    # Save all data
    output_filename = f"work_records_{datetime.now().strftime('%Y%m%d')}.json"
    extractor.save_to_json(all_data, output_filename)
    
    # Add step to save to database
    extractor.save_to_database(all_data)

if __name__ == "__main__":
    main() 