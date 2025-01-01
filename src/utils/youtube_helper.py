import os
import json
import time
import threading
import requests
from functools import wraps
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
from yt_dlp import YoutubeDL
from pytube import YouTube
from selenium.webdriver.common.keys import Keys

class TimeoutError(Exception):
    pass

def timeout(seconds):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = []
            error = []
            
            def target():
                try:
                    result.append(func(*args, **kwargs))
                except Exception as e:
                    error.append(e)
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)
            
            if thread.is_alive():
                raise TimeoutError(f"函数执行超过 {seconds} 秒")
            
            if error:
                raise error[0]
                
            return result[0] if result else None
            
        return wrapper
    return decorator

class YouTubeHelper:
    def __init__(self, openai_api_key=None):
        """初始化YouTube助手"""
        # 加载环境变量
        load_dotenv()
        
        # 获取API密钥
        self.openai_api_key = openai_api_key
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        
        if not self.youtube_api_key:
            raise ValueError("未找到 YOUTUBE_API_KEY 环境变量")
            
        # 初始化 OpenAI 客户端
        self.openai_client = OpenAI(api_key=openai_api_key)
        
        # YouTube API 基础 URL
        self.youtube_api_base = "https://www.googleapis.com/youtube/v3"
        
        # 创建必要的目录
        for dir_path in ['data/downloads', 'data/audios', 'data/transcripts', 'data/articles']:
            os.makedirs(dir_path, exist_ok=True)

    @timeout(300)  # 5分钟超时
    def search_videos(self, query, max_results=5):
        """使用 YouTube API 搜索视频"""
        try:
            print(f"开始搜索视频，关键词: {query}")
            
            # 构建搜索请求
            search_url = f"{self.youtube_api_base}/search"
            params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': max_results,
                'key': self.youtube_api_key,
                'videoEmbeddable': True,
                'videoSyndicated': True,
                'videoDuration': 'short',  # 只搜索短视频
                'fields': 'items(id/videoId,snippet/title,snippet/description)'
            }
            
            # 发送搜索请求
            print("正在获取搜索结果...")
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            search_results = response.json()
            if 'items' not in search_results:
                print("搜索返回空结果")
                return []
                
            # 获取视频详细信息
            videos = []
            for item in search_results['items']:
                video_id = item['id']['videoId']
                
                # 获取视频统计信息
                video_url = f"{self.youtube_api_base}/videos"
                video_params = {
                    'part': 'statistics,contentDetails',
                    'id': video_id,
                    'key': self.youtube_api_key
                }
                
                video_response = requests.get(video_url, params=video_params)
                video_response.raise_for_status()
                
                video_data = video_response.json()
                if not video_data.get('items'):
                    continue
                    
                video_info = video_data['items'][0]
                
                # 解析视频时长
                duration = video_info['contentDetails']['duration']  # 格式如 "PT1H2M10S"
                duration_sec = self._parse_duration(duration)
                
                video = {
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'duration': duration_sec,
                    'view_count': int(video_info['statistics'].get('viewCount', 0))
                }
                
                videos.append(video)
                print(f"找到视频: {video['title']}")
            
            return videos
            
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {str(e)}")
            return []
        except Exception as e:
            print(f"搜索视频时出错: {str(e)}")
            return []
            
    def _parse_duration(self, duration: str) -> int:
        """解析 ISO 8601 时长格式"""
        import re
        import isodate
        try:
            return int(isodate.parse_duration(duration).total_seconds())
        except:
            # 备用解析方法
            hours = re.search(r'(\d+)H', duration)
            minutes = re.search(r'(\d+)M', duration)
            seconds = re.search(r'(\d+)S', duration)
            
            total_seconds = 0
            if hours:
                total_seconds += int(hours.group(1)) * 3600
            if minutes:
                total_seconds += int(minutes.group(1)) * 60
            if seconds:
                total_seconds += int(seconds.group(1))
                
            return total_seconds

    @timeout(300)  # 5分钟超时
    def download_video(self, video_url):
        """使用 yt-dlp 下载YouTube视频"""
        try:
            print(f"\n开始下载视频: {video_url}")
            
            # 创建下载目录
            download_dir = os.path.abspath(os.path.join('data', 'downloads'))
            os.makedirs(download_dir, exist_ok=True)
            
            # 配置下载选项
            ydl_opts = {
                'format': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]/best',  # 更灵活的格式选择
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
                'extract_flat': False,
                'socket_timeout': 30,
                'retries': 3,
                'fragment_retries': 3,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                'merge_output_format': 'mp4',  # 确保输出为 mp4 格式
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4'
                }]
            }
            
            # 下载视频
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                video_path = ydl.prepare_filename(info)
            
            # 验证下载结果
            if os.path.exists(video_path):
                file_size = os.path.getsize(video_path)
                if file_size < 1024:  # 小于1KB
                    print(f"\n❌ 下载的文件过小 ({file_size} bytes)，可能是下载失败")
                    os.remove(video_path)
                    return None
                
                print(f"\n✅ 下载成功: {video_path}")
                print(f"文件大小: {file_size / (1024*1024):.2f} MB")
                return video_path
            else:
                print("\n❌ 下载失败：找不到下载的文件")
                return None
            
        except Exception as e:
            print(f"\n下载失败: {str(e)}")
            print(f"错误类型: {type(e).__name__}")
            raise Exception("视频下载失败")

    @timeout(180)  # 3分钟超时
    def convert_to_audio(self, video_path):
        """将视频转换为音频"""
        try:
            if not os.path.exists(video_path):
                print(f"视频文件不存在: {video_path}")
                return None
            
            os.makedirs('data/audios', exist_ok=True)
            
            audio_path = os.path.join(
                'data/audios',
                os.path.splitext(os.path.basename(video_path))[0] + '.mp3'
            )
            
            import subprocess
            command = [
                'ffmpeg',
                '-i', video_path,
                '-vn',
                '-acodec', 'libmp3lame',
                '-ab', '128k',
                '-ar', '44100',
                '-y',
                audio_path
            ]
            
            print("\n开始转换音频...")
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode == 0:
                if os.path.exists(audio_path):
                    file_size = os.path.getsize(audio_path)
                    if file_size < 1024:
                        print(f"\n❌ 转换后的音频文件过小 ({file_size} bytes)，可能是转换失败")
                        os.remove(audio_path)
                        return None
                        
                    print(f"\n✅ 音频转换成功: {audio_path}")
                    print(f"文件大小: {file_size / (1024*1024):.2f} MB")
                    return audio_path
            else:
                print(f"\n❌ 音频转换失败: {result.stderr}")
                return None
            
        except subprocess.TimeoutExpired:
            print("FFmpeg 转换操作超时")
            return None
        except Exception as e:
            print(f"转换音频时出错: {str(e)}")
            if os.path.exists(audio_path):
                os.remove(audio_path)
            return None

    @timeout(600)  # 10分钟超时
    def convert_audio_to_text(self, audio_path):
        """使用 OpenAI Whisper API 转换音频为文字"""
        try:
            if not os.path.exists(audio_path):
                print(f"音频文件不存在: {audio_path}")
                return None
                
            print("开始转换音频为文字...")
            print("使用AI模型: OpenAI Whisper")
            
            file_size = os.path.getsize(audio_path)
            max_size = 25 * 1024 * 1024  # 25MB
            
            if file_size > max_size:
                print(f"音频文件过大 ({file_size / (1024*1024):.2f} MB)，需要分割处理")
                audio = AudioSegment.from_mp3(audio_path)
                duration = len(audio)
                chunk_duration = 5 * 60 * 1000  # 5分钟
                chunks = []
                
                for i in range(0, duration, chunk_duration):
                    chunk = audio[i:i + chunk_duration]
                    chunk_path = f"{audio_path}.chunk{i//chunk_duration}.mp3"
                    chunk.export(chunk_path, format="mp3")
                    chunks.append(chunk_path)
                
                texts = []
                for chunk_path in chunks:
                    with open(chunk_path, 'rb') as audio_file:
                        try:
                            response = self.openai_client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                                response_format="text"
                            )
                            texts.append(response)
                        except Exception as e:
                            print(f"处理分片 {chunk_path} 时出错: {str(e)}")
                    os.remove(chunk_path)
                
                return " ".join(texts) if texts else None
            else:
                with open(audio_path, 'rb') as audio_file:
                    response = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )
                    return response
            
        except TimeoutError:
            print("音频转文字操作超时")
            return None
        except Exception as e:
            print(f"转换音频为文字时出错: {str(e)}")
            return None