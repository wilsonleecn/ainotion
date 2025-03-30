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
            print(f"正在尝试访问数据库: {database_id}")
            response = self.notion.databases.query(
                database_id=database_id,
                sorts=[{
                    "timestamp": "created_time",
                    "direction": "descending"
                }]
            )
            
            # 打印数据库结构信息
            if 'results' in response and len(response['results']) > 0:
                print("成功获取数据库内容")
                first_page = response['results'][0]
                print("数据库列名:", list(first_page['properties'].keys()))
            else:
                print("数据库是空的或没有权限访问内容")
            
            return response['results']
        except Exception as e:
            print(f"获取数据库内容时出错: {str(e)}")
            print(f"错误类型: {type(e)}")
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
    NOTION_TOKEN = "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"
    
    notion = Client(auth=NOTION_TOKEN)
    
    def print_database_info(database_id, level=0):
        """递归打印数据库及其子数据库的信息"""
        try:
            # 获取数据库中的页面
            response = notion.databases.query(database_id=database_id)
            
            # 遍历所有页面
            for page in response['results']:
                # 检查页面是否包含子数据库s
                sub_pages = notion.blocks.children.list(block_id=page['id'])
                for block in sub_pages['results']:
                    if block['type'] == 'child_database':
                        indent = "  " * level
                        print(f"{indent}子数据库ID: {block['id']}")
                        print(f"{indent}子数据库标题: {block['child_database']['title']}")
                        print(f"{indent}---")
                        # 递归访问子数据库
                        print_database_info(block['id'], level + 1)
        except Exception as e:
            print(f"访问数据库 {database_id} 时出错: {str(e)}")
    
    # 列出所有顶级数据库
    try:
        response = notion.search(filter={"property": "object", "value": "database"})
        print("数据库层级结构：")
        for item in response['results']:
            print(f"顶级数据库ID: {item['id']}")
            print(f"顶级数据库标题: {item['title'][0]['plain_text'] if item['title'] else 'Untitled'}")
            print("---")
            # 递归查找子数据库
            print_database_info(item['id'])
    except Exception as e:
        print(f"搜索数据库时出错: {str(e)}")

if __name__ == "__main__":
    main() 