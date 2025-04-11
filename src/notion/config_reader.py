import os

class Config:
    # OpenAI configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    # Notion configuration
    # NOTION_TOKEN = "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"
    NOTION_TOKEN = os.getenv('NOTION_TOKEN')
