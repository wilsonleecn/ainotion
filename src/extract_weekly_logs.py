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
        Returns (monday_date, sunday_date)
        """
        if date is None:
            date = datetime.now()
        elif isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')

        # Get the most recent Monday
        monday = date - timedelta(days=date.weekday())
        
        # If today is Sunday or Monday, get the previous week
        if date.weekday() in [0, 6]:
            monday = monday - timedelta(days=7)
            
        sunday = monday + timedelta(days=6)
        return monday, sunday

    def get_work_logs_by_date_range(self, start_date, end_date):
        """
        Get work logs between start_date and end_date
        Returns simplified JSON object with work logs
        """
        # Convert dates to datetime if they're strings
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Format dates for searching
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(f"Work Log {current_date.strftime('%Y%m%d')}")
            current_date += timedelta(days=1)

        work_logs = {}
        
        # Search for each daily work log
        for date_title in date_range:
            response = self.notion.search(
                query=date_title,
                filter={"property": "object", "value": "page"}
            )
            
            for page in response['results']:
                title = self._get_page_title(page)
                if title == date_title:
                    database_id = self.find_database_in_page(page['id'])
                    if database_id:
                        records = self.extract_database_content(database_id)
                        if records:  # Only add pages that have records
                            work_logs[title] = {
                                'title': title,
                                'records': records
                            }
        
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
            children = self.notion.blocks.children.list(block_id=page_id)
            for block in children['results']:
                if block['type'] == 'child_database':
                    return block['id']
            return None
        except Exception:
            return None

    def extract_database_content(self, database_id):
        """Extract simplified database content"""
        try:
            response = self.notion.databases.query(database_id=database_id)
            
            simplified_records = []
            for record in response['results']:
                processed = self._process_record(record)
                if processed['properties']:  # Only add records with properties
                    simplified_record = {
                        'id': record['id'],
                        'properties': processed['properties']
                    }
                    simplified_records.append(simplified_record)
            
            return simplified_records
            
        except Exception:
            return []

    def _process_record(self, record):
        """Process database record with simplified output"""
        processed = {
            'id': record['id'],
            'properties': {}
        }
        
        for prop_name, prop_data in record['properties'].items():
            value = self._extract_property_value(prop_data)
            if value:  # Only include properties with values
                processed['properties'][prop_name] = value
                
        return processed

    def _extract_property_value(self, prop_data):
        """Extract property value with simplified output"""
        prop_type = prop_data['type']
        
        if prop_type == 'title':
            return self._extract_rich_text(prop_data['title'])
        elif prop_type == 'rich_text':
            return self._extract_rich_text(prop_data['rich_text'])
        elif prop_type == 'date':
            return prop_data['date']['start'] if prop_data['date'] else None
        elif prop_type == 'select':
            return prop_data['select']['name'] if prop_data['select'] else None
        elif prop_type == 'multi_select':
            return [item['name'] for item in prop_data['multi_select']]
        elif prop_type == 'checkbox':
            return prop_data['checkbox']
        elif prop_type == 'number':
            return prop_data['number']
        return None

    def _extract_rich_text(self, rich_text_array):
        """Extract rich text content"""
        if not rich_text_array:
            return ""
        return " ".join(text['plain_text'] for text in rich_text_array)

def main():
    NOTION_TOKEN = "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"
    
    extractor = WeeklyWorkLogExtractor(NOTION_TOKEN)
    
    # Get the latest complete week's date range
    start_date, end_date = extractor.get_latest_complete_week()
    
    # Get work logs for the date range
    work_logs = extractor.get_work_logs_by_date_range(start_date, end_date)
    
    # Output JSON to stdout
    print(json.dumps(work_logs, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main() 