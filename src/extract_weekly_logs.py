import os
from notion_client import Client
from datetime import datetime, timedelta
import json
import re

class WeeklyWorkLogExtractor:
    def __init__(self, token):
        """Initialize Notion client"""
        self.notion = Client(auth=token)

    def get_latest_complete_week(self, date=None):
        """
        Get the start and end dates of the latest complete week before the given date
        If no date provided, use current date
        Returns (monday_date, sunday_date) where both dates are at midnight (00:00:00)
        """
        if date is None:
            date = datetime.now()
        elif isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')
        print(f"date: {date}")
        # 获取上周一的日期
        # 如果今天是周日(6)，减去7天得到上周日，再减去6天得到上周一
        # 如果是其他日子，先回到本周一，再减去7天得到上周一
        print(f"date.weekday(): {date.weekday()}")
        if date.weekday() == 6:  # 周日
            monday = date - timedelta(days=13)
        else:
            # 先回到本周一，再减去7天
            monday = date - timedelta(days=date.weekday()) - timedelta(days=7)
        # 从周一开始加6天得到周日
        sunday = monday + timedelta(days=6)
        print(f"sunday: {sunday}")
        # Set both dates to midnight
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        sunday = (monday + timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        print(f"monday: {monday}")
        print(f"sunday: {sunday}")
        return monday, sunday

    def get_work_logs_by_date_range(self, start_date, end_date):
        """
        Get work logs between start_date and end_date
        Returns simplified JSON object with work logs
        """
        print(f"\nSearching work logs from {start_date} to {end_date}")
        
        # Convert dates to datetime if they're strings
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        print(f"Start date (after conversion): {start_date}")
        print(f"End date (after conversion): {end_date}")

        # Format dates for searching - modified to use YYYYMM format
        date_range = set()  # Using set to avoid duplicates
        current_date = start_date
        while current_date <= end_date:
            formatted_date = f"Work Log {current_date.strftime('%Y%m')}"
            date_range.add(formatted_date)
            current_date += timedelta(days=1)

        print(f"Looking for pages with titles: {date_range}")
        work_logs = {}
        
        # Search for each monthly work log
        for date_title in date_range:
            print(f"\nSearching for: {date_title}")
            response = self.notion.search(
                query=date_title,
                filter={"property": "object", "value": "page"}
            )
            
            print(f"Found {len(response['results'])} results")
            
            for page in response['results']:
                title = self._get_page_title(page)
                print(f"Processing page with title: {title}")
                
                # Changed to check if the title matches the monthly format
                if title == date_title:
                    database_id = self.find_database_in_page(page['id'])
                    print(f"Database ID found: {database_id}")
                    
                    if database_id:
                        all_records = self.extract_database_content(database_id, start_date, end_date)
                        # Filter records within the date range
                        filtered_records = []
                        for record in all_records:
                            props = record.get('properties', {})
                            timestamp = props.get('timestamp', {})
                            if timestamp and timestamp.get('date', {}).get('start'):
                                record_date = datetime.fromisoformat(timestamp['date']['start'].replace('Z', '+00:00')).replace(tzinfo=None)
                                if start_date <= record_date <= end_date:
                                    # Get rich_text content
                                    note_text = props.get('Note', {}).get('rich_text', [{}])[0].get('plain_text', '') if props.get('Note', {}).get('rich_text') else ''
                                    request_from_text = props.get('Request from', {}).get('rich_text', [{}])[0].get('plain_text', '') if props.get('Request from', {}).get('rich_text') else ''
                                    
                                    # Simplify record structure
                                    simplified_record = {
                                        'timestamp': timestamp['date']['start'],
                                        'title': props.get('Title', {}).get('title', [{}])[0].get('plain_text', ''),
                                        'type': props.get('Type', {}).get('multi_select', []),
                                        'status': props.get('Status', {}).get('select', {}).get('name', ''),
                                        'note': note_text,
                                        'co-worker': props.get('Co-worker', {}).get('multi_select', []),
                                        'request_from': request_from_text
                                    }
                                    filtered_records.append(simplified_record)
                        
                        print(f"Extracted {len(all_records)} records, {len(filtered_records)} within date range")
                        
                        if filtered_records:  # Only add pages that have filtered records
                            work_logs[title] = {
                                'title': title,
                                'records': filtered_records
                            }
        
        print(f"\nTotal work logs found: {len(work_logs)}")
        return work_logs

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
            print(f"Looking for database in page: {page_id}")
            children = self.notion.blocks.children.list(block_id=page_id)
            for block in children['results']:
                if block['type'] == 'child_database':
                    print(f"Found database with ID: {block['id']}")
                    return block['id']
            print("No database found in page")
            return None
        except Exception as e:
            print(f"Error finding database: {str(e)}")
            return None

    def extract_database_content(self, database_id, start_date, end_date):
        try:
            filter_condition = {
                "property": "timestamp",
                "date": {
                    "after": start_date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
                    "before": (end_date.replace(hour=23, minute=59, second=59, microsecond=999999) + timedelta(days=1)).isoformat()
                }
            }

            response = self.notion.databases.query(
                database_id=database_id,
                filter=filter_condition
            )
            return response.get('results', [])

        except Exception as e:
            print(f"Error extracting database content: {e}")
            return []

def main():
    NOTION_TOKEN = "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"
    
    extractor = WeeklyWorkLogExtractor(NOTION_TOKEN)
    
    # Get the latest complete week's date range
    start_date, end_date = extractor.get_latest_complete_week()
    print(f"\nLatest complete week: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Get work logs for the date range
    work_logs = extractor.get_work_logs_by_date_range(start_date, end_date)
    
    # Output JSON to stdout
    print("\nFinal output:")
    print(json.dumps(work_logs, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main() 