import unittest
import os
import time
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.utils.youtube_helper import YouTubeHelper

class TestYouTubeHelper(unittest.TestCase):
    def setUp(self):
        self.youtube_helper = YouTubeHelper(proxy=None)  # 不使用代理
        
    def test_search_videos(self):
        print("\n测试搜索视频功能...")
        query = "Python programming tutorial short"
        results = self.youtube_helper.search_videos(query, max_results=2)
        
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        if results:
            print(f"找到 {len(results)} 个视频:")
            for video in results:
                print(f"标题: {video['title']}")
                print(f"URL: {video['url']}")
                print("---")
    
    def test_download_and_convert(self):
        print("\n测试下载和转换功能...")
        # 使用一个较短的视频进行测试
        video_url = "https://www.youtube.com/watch?v=_Z5-P9v3F8w"  # 使用一个短视频（约30秒）
        
        # 测试下载视频
        start_time = time.time()
        video_path = self.youtube_helper.download_video(video_url)
        download_time = time.time() - start_time
        print(f"下载耗时: {download_time:.2f} 秒")
        
        self.assertIsNotNone(video_path)
        self.assertTrue(os.path.exists(video_path))
        self.assertLess(download_time, 300, "下载超时")  # 确保下载时间不超过5分钟
        print(f"视频下载成功: {video_path}")
        
        # 测试转换为音频
        if video_path:
            start_time = time.time()
            audio_path = self.youtube_helper.convert_to_audio(video_path)
            convert_time = time.time() - start_time
            print(f"转换耗时: {convert_time:.2f} 秒")
            
            self.assertIsNotNone(audio_path)
            self.assertTrue(os.path.exists(audio_path))
            self.assertLess(convert_time, 180, "音频转换超时")  # 确保转换时间不超过3分钟
            print(f"音频转换成功: {audio_path}")
            
            # 测试音频转文字
            if audio_path:
                start_time = time.time()
                text = self.youtube_helper.convert_audio_to_text(audio_path)
                transcribe_time = time.time() - start_time
                print(f"转写耗时: {transcribe_time:.2f} 秒")
                
                self.assertIsNotNone(text)
                self.assertLess(transcribe_time, 600, "音频转文字超时")  # 确保转写时间不超过10分钟
                print("音频转文字结果:")
                print(text)
    
    def test_timeout_handling(self):
        print("\n测试超时处理...")
        # 测试一个不存在的视频URL（应该会触发超时）
        video_url = "https://www.youtube.com/watch?v=invalid_video_id"
        
        start_time = time.time()
        video_path = self.youtube_helper.download_video(video_url)
        download_time = time.time() - start_time
        
        self.assertIsNone(video_path)  # 应该返回 None
        self.assertLess(download_time, 310, "超时处理应该在5分钟内完成")  # 允许有10秒的缓冲时间

if __name__ == '__main__':
    unittest.main() 