import os
from notion_client import Client
from datetime import datetime

class NotionArticleExtractor:
    def __init__(self, token):
        """初始化Notion客户端"""
        self.notion = Client(auth=token)
    
    def get_database_content(self, database_id):
        """获取指定数据库中的所有文章"""
        try:
            # 查询数据库
            response = self.notion.databases.query(
                database_id=database_id,
                sorts=[{
                    "timestamp": "created_time",
                    "direction": "descending"
                }]
            )
            
            return response['results']
        except Exception as e:
            print(f"获取数据库内容时出错: {str(e)}")
            return []
    
    def extract_page_content(self, page_id):
        """提取页面内容"""
        try:
            blocks = self.notion.blocks.children.list(block_id=page_id)
            content = []
            
            for block in blocks['results']:
                if block['type'] == 'paragraph':
                    if block['paragraph']['rich_text']:
                        content.append(block['paragraph']['rich_text'][0]['plain_text'])
                elif block['type'] == 'heading_1':
                    if block['heading_1']['rich_text']:
                        content.append(f"# {block['heading_1']['rich_text'][0]['plain_text']}")
                elif block['type'] == 'heading_2':
                    if block['heading_2']['rich_text']:
                        content.append(f"## {block['heading_2']['rich_text'][0]['plain_text']}")
                elif block['type'] == 'heading_3':
                    if block['heading_3']['rich_text']:
                        content.append(f"### {block['heading_3']['rich_text'][0]['plain_text']}")
                
            return '\n\n'.join(content)
        except Exception as e:
            print(f"提取页面内容时出错: {str(e)}")
            return ""
    
    def save_to_file(self, title, content, output_dir="articles"):
        """将内容保存到文件"""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 清理文件名
            safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
            filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d')}.md"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"文章已保存: {filepath}")
        except Exception as e:
            print(f"保存文件时出错: {str(e)}")

def main():
    # 替换为您的Notion API密钥
    NOTION_TOKEN = "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"
    # 替换为您的数据库ID
    DATABASE_ID = "113c04e7666e808abddbcf45ae97e86b"
    
    extractor = NotionArticleExtractor(NOTION_TOKEN)
    
    # 获取数据库中的所有页面
    pages = extractor.get_database_content(DATABASE_ID)
    
    for page in pages:
        try:
            # 获取页面标题
            title = page['properties']['Name']['title'][0]['plain_text']
            # 获取页面内容
            content = extractor.extract_page_content(page['id'])
            # 保存文章
            extractor.save_to_file(title, content)
        except Exception as e:
            print(f"处理页面时出错: {str(e)}")
            continue

if __name__ == "__main__":
    main() 