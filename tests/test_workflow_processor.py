import unittest
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.workflow_processor import WorkflowProcessor

class TestWorkflowProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = WorkflowProcessor()
        
        # 确保测试目录存在
        for dir_path in ['data/downloads', 'data/audios', 'data/transcripts', 'data/articles']:
            os.makedirs(dir_path, exist_ok=True)
    
    def test_analyze_user_requirement(self):
        print("\n测试需求分析...")
        topic = "Python编程入门教程"
        keywords = self.processor.analyze_user_requirement(topic)
        
        self.assertIsNotNone(keywords)
        self.assertIsInstance(keywords, str)
        self.assertTrue(len(keywords) > 0)
        print(f"生成的关键词: {keywords}")
    
    def test_score_video(self):
        print("\n测试视频评分...")
        topic = "Python编程入门"
        video_info = {
            'title': 'Python Tutorial for Beginners',
            'description': 'Learn Python programming from scratch',
            'duration': 600,  # 10分钟
            'view_count': 10000
        }
        
        score = self.processor.score_video(topic, video_info)
        
        self.assertIsInstance(score, float)
        self.assertTrue(0 <= score <= 10)
        print(f"视频评分: {score}")
    
    def test_generate_article(self):
        print("\n测试文章生成...")
        transcript = """
        今天我们来学习Python编程的基础知识。
        首先，Python是一个非常简单易学的编程语言。
        它的语法清晰，代码可读性强。
        让我们从Hello World开始吧！
        """
        
        # 测试公众号文章模式
        article = self.processor.generate_article(transcript, "1")
        self.assertIsNotNone(article)
        self.assertTrue(len(article) > len(transcript))
        print("生成的公众号文章长度:", len(article))
        
        # 测试文字稿模式
        transcript = self.processor.generate_article(transcript, "2")
        self.assertIsNotNone(transcript)
        print("生成的文字稿长度:", len(transcript))
    
    def test_review_article(self):
        print("\n测试文章审核...")
        article = """
        # Python入门教程
        
        大家好，今天我们来学习Python编程的基础知识。
        
        ## 为什么选择Python
        
        Python是一个非常简单易学的编程语言，它的语法清晰，代码可读性强。
        
        ## 开始学习
        
        让我们从Hello World开始吧！
        """
        
        status, suggestions = self.processor.review_article(article)
        
        self.assertIsInstance(status, str)
        self.assertIsInstance(suggestions, list)
        print(f"审核状态: {status}")
        if suggestions:
            print("审核建议:")
            for suggestion in suggestions:
                print(f"- {suggestion}")
    
    def test_complete_workflow(self):
        print("\n测试完整工作流...")
        topic = "Python快速入门教程"
        
        # 测试公众号文章模式
        result = self.processor.process_workflow(topic, "1")
        self.assertIsNotNone(result)
        print("公众号文章生成完成")
        
        # 测试文字稿模式
        result = self.processor.process_workflow(topic, "2")
        self.assertIsNotNone(result)
        print("文字稿生成完成")

if __name__ == '__main__':
    unittest.main() 