import os
import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from pydub import AudioSegment
import yt_dlp
import openai
from openai import OpenAI
from dotenv import load_dotenv
from utils.zhuanxie import transcribe_audio

class YouTubeHelper:
    def __init__(self):
        # 加载环境变量
        load_dotenv()
        
        # 获取 API 密钥
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # 初始化 OpenAI 客户端
        self.client = OpenAI(api_key=self.openai_api_key)
        
        # 初始化 Chrome 选项
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        
        # 创建下载目录
        self.download_dir = 'downloads'
        os.makedirs(self.download_dir, exist_ok=True)
        
    def search_videos(self, query):
        """使用 YouTube API 搜索视频"""
        try:
            url = f"https://www.googleapis.com/youtube/v3/search"
            params = {
                'key': self.youtube_api_key,
                'q': query,
                'part': 'snippet',
                'maxResults': 5,
                'type': 'video'
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            videos = []
            for item in data.get('items', []):
                videos.append({
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'duration': 0,
                    'view_count': 0
                })
            
            return videos
            
        except Exception as e:
            print(f"搜索视频时出错: {str(e)}")
            return None

    def download_video(self, url):
        """下载视频"""
        try:
            # 配置 yt-dlp 选项
            ydl_opts = {
                'format': 'best',  # 下载最佳质量
                'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [self._download_progress_hook],
            }
            
            # 使用 yt-dlp 下载视频
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                print(f"\n视频已下载: {filename}")
                return filename
                
        except Exception as e:
            print(f"下载视频时出错: {str(e)}")
            return None
    
    def _download_progress_hook(self, d):
        """下载进度回调函数"""
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            
            if total_bytes:
                progress = int(50 * downloaded_bytes / total_bytes)
                print(f"\r下载进度: [{'=' * progress}{' ' * (50-progress)}] {downloaded_bytes}/{total_bytes}", end='')

    def convert_to_audio(self, video_path):
        """转换视频为音频"""
        try:
            if not os.path.exists(video_path):
                print(f"视频文件不存在: {video_path}")
                return None
                
            audio_path = video_path.rsplit('.', 1)[0] + '.mp3'
            video = AudioSegment.from_file(video_path)
            video.export(audio_path, format='mp3')
            print(f"音频已保存: {audio_path}")
            return audio_path
        except Exception as e:
            print(f"转换音频时出错: {str(e)}")
            return None

    def convert_audio_to_text(self, audio_path):
        """转换音频为文字"""
        try:
            if not os.path.exists(audio_path):
                print(f"音频文件不存在: {audio_path}")
                return None
                
            print("开始转换音频为文字...")
            response = transcribe_audio(audio_path)
            return response
            
        except Exception as e:
            print(f"转换音频为文字时出错: {str(e)}")
            return None
        
if __name__ == "__main__":
    print("请选择要测试的功能")
    print("1. 搜索视频")
    print("2. 下载视频")
    print("3. 转换音频为文字")
    choice = input("请输入要测试的功能编号: ")
    
    if choice == "3":
        YouTubeHelper.convert_audio_to_text("downloads/文稿-20250104-160000.mp3")