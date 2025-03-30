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
    
    def print_page_info(page, level=0):
        """打印页面信息"""
        indent = "  " * level
        # 获取页面标题
        title = "Untitled"
        if 'properties' in page:
            # 尝试不同的标题属性名
            title_props = ['Name', 'title', 'Title']
            for prop_name in title_props:
                if prop_name in page['properties']:
                    title_array = page['properties'][prop_name].get('title', [])
                    if title_array:
                        title = title_array[0]['plain_text']
                        break
        
        print(f"{indent}页面ID: {page['id']}")
        print(f"{indent}页面标题: {title}")
        print(f"{indent}创建时间: {page['created_time']}")
        print(f"{indent}最后编辑时间: {page['last_edited_time']}")
        
        try:
            # 获取子页面
            children = notion.blocks.children.list(block_id=page['id'])
            has_children = False
            
            for block in children['results']:
                if block['type'] in ['child_page', 'child_database']:
                    has_children = True
                    print(f"{indent}  └─ 子{block['type']}: {block['id']}")
                    if block['type'] == 'child_page':
                        # 递归获取子页面信息
                        sub_page = notion.pages.retrieve(page_id=block['id'])
                        print_page_info(sub_page, level + 2)
            
            if has_children:
                print(f"{indent}---")
                
        except Exception as e:
            print(f"{indent}获取子页面时出错: {str(e)}")
    
    # 使用search API获取所有页面
    try:
        print("所有可访问的页面：")
        print("================")
        
        # 初始化游标
        start_cursor = None
        while True:
            # 搜索页面
            response = notion.search(
                filter={"property": "object", "value": "page"},
                start_cursor=start_cursor,
                page_size=100  # 每次获取100个结果
            )
            
            # 打印当前批次的页面信息
            for page in response['results']:
                print_page_info(page)
                print("---")
            
            # 检查是否还有更多结果
            if not response.get('has_more'):
                break
                
            # 更新游标以获取下一批结果
            start_cursor = response.get('next_cursor')
            
    except Exception as e:
        print(f"搜索页面时出错: {str(e)}")

if __name__ == "__main__":
    main() 