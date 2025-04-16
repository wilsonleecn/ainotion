import os

class Config:
    # OpenAI configuration
    AI_ENGIN_API_KEY = os.getenv('AI_ENGIN_API_KEY')
    AI_ENGIN_BASE_URL = os.getenv('AI_ENGIN_BASE_URL')
    # Notion configuration
    # NOTION_TOKEN = "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"
    NOTION_TOKEN = os.getenv('NOTION_TOKEN')
