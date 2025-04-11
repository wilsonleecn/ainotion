import os
from notion_client import Client
from datetime import datetime, timedelta
import json
import re
from config_reader import Config

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
        # Get last Monday's date
        # If today is Sunday(6), subtract 13 days to get last Monday
        # For other days, first go back to this Monday, then subtract 7 days
        if date.weekday() == 6:  # Sunday
            monday = date - timedelta(days=13)
        else:
            # First go back to this Monday, then subtract 7 days
            monday = date - timedelta(days=date.weekday()) - timedelta(days=7)
        # Add 6 days to Monday to get Sunday
        sunday = monday + timedelta(days=6)
        # Set both dates to midnight
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        sunday = (monday + timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        return monday, sunday

    def get_work_logs_by_date_range(self, start_date, end_date):
        """
        Get work logs between start_date and end_date
        Returns array of work logs sorted by timestamp
        """
        print(f"\nSearching work logs from {start_date} to {end_date}")
        
        # Convert dates to datetime if they're strings
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Format dates for searching - modified to use YYYYMM format
        date_range = set()  # Using set to avoid duplicates
        current_date = start_date
        while current_date <= end_date:
            formatted_date = f"Work Log {current_date.strftime('%Y%m')}"
            date_range.add(formatted_date)
            current_date += timedelta(days=1)

        print(f"Looking for pages with titles: {date_range}")
        all_records = []  # Store all records here instead of using work_logs dict
        
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
                
                if title == date_title:
                    database_id = self.find_database_in_page(page['id'])
                    print(f"Database ID found: {database_id}")
                    
                    if database_id:
                        records = self.extract_database_content(database_id, start_date, end_date)
                        # Filter records within the date range
                        for record in records:
                            props = record.get('properties', {})
                            timestamp = props.get('timestamp', {})
                            if timestamp and timestamp.get('date', {}).get('start'):
                                record_date = datetime.fromisoformat(timestamp['date']['start'].replace('Z', '+00:00')).replace(tzinfo=None)
                                if start_date <= record_date <= end_date:
                                    # Get rich_text content
                                    note_text = props.get('Note', {}).get('rich_text', [{}])[0].get('plain_text', '') if props.get('Note', {}).get('rich_text') else ''
                                    request_from_text = props.get('Request from', {}).get('rich_text', [{}])[0].get('plain_text', '') if props.get('Request from', {}).get('rich_text') else ''
                                    
                                    # Extract type names from multi_select
                                    type_names = [t.get('name', '') for t in props.get('Type', {}).get('multi_select', [])]
                                    # Extract co-worker names from multi_select
                                    coworker_names = [c.get('name', '') for c in props.get('Co-worker', {}).get('multi_select', [])]
                                    
                                    # Simplify record structure
                                    simplified_record = {
                                        'timestamp': timestamp['date']['start'],
                                        'title': props.get('Title', {}).get('title', [{}])[0].get('plain_text', ''),
                                        'type': type_names,
                                        'status': props.get('Status', {}).get('select', {}).get('name', ''),
                                        'note': note_text,
                                        'co-worker': coworker_names,
                                        'request_from': request_from_text
                                    }
                                    all_records.append(simplified_record)
        
        # Sort records by timestamp
        all_records.sort(key=lambda x: x['timestamp'])
        
        print(f"\nTotal records found: {len(all_records)}")
        return all_records

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
    extractor = WeeklyWorkLogExtractor(Config.NOTION_TOKEN)
    
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