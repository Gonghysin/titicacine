import os
from utils.openai_helper import OpenAIHelper

class ArticleReviewer:
    def __init__(self):
        print("初始化文章审核工具...")
        self.openai_helper = OpenAIHelper()
        self.articles_dir = 'articles'
        
    def list_articles(self):
        """列出所有文章"""
        try:
            # 获取所有 .md 文件
            articles = [f for f in os.listdir(self.articles_dir) if f.endswith('.md')]
            
            if not articles:
                print("没有找到任何文章！")
                return None
            
            print("\n找到以下文章：")
            for i, article in enumerate(articles, 1):
                print(f"{i}. {article}")
            
            return articles
            
        except Exception as e:
            print(f"列出文章时出错: {str(e)}")
            return None
    
    def select_article(self, articles):
        """让用户选择要审核的文章"""
        while True:
            try:
                choice = input("\n请输入要审核的文章编号: ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(articles):
                    return articles[idx]
                print("无效的选择，请重试")
            except ValueError:
                print("请输入有效的数字")
    
    def review_article(self, article_name):
        """审核选定的文章"""
        try:
            # 读取文章内容
            file_path = os.path.join(self.articles_dir, article_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n开始审核文章: {article_name}")
            reviewed_content = self.openai_helper.review_article(content)
            
            if not reviewed_content:
                print("审核失败")
                return
            
            # 保存审核后的文章
            reviewed_path = os.path.join(
                self.articles_dir, 
                f"审核后-{article_name}"
            )
            
            with open(reviewed_path, 'w', encoding='utf-8') as f:
                f.write(reviewed_content)
            
            print(f"\n审核完成！新文件已保存: {reviewed_path}")
            
        except Exception as e:
            print(f"审核文章时出错: {str(e)}")
    
    def run(self):
        """运行审核流程"""
        try:
            # 1. 列出所有文章
            articles = self.list_articles()
            if not articles:
                return
            
            # 2. 选择文章
            selected = self.select_article(articles)
            
            # 3. 审核文章
            self.review_article(selected)
            
        except Exception as e:
            print(f"运行审核流程时出错: {str(e)}")

if __name__ == "__main__":
    reviewer = ArticleReviewer()
    reviewer.run() 