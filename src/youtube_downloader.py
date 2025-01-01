import os
from typing import Dict, Any, List
from youtube_search import YoutubeSearch
from yt_dlp import YoutubeDL

class YouTubeDownloader:
    def __init__(self):
        """
        初始化YouTube下载器
        """
        self.download_path = "downloads"
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
    
    def search_videos(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索YouTube视频
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数
            
        Returns:
            视频列表
        """
        try:
            results = YoutubeSearch(query, max_results=max_results).to_dict()
            return results
        except Exception as e:
            raise Exception(f"搜索视频时出错: {str(e)}")
    
    def download_audio(self, video_id: str) -> str:
        """
        下载视频的音频
        
        Args:
            video_id: 视频ID
            
        Returns:
            音频文件路径
        """
        try:
            output_path = os.path.join(self.download_path, f"{video_id}.mp3")
            
            # 如果文件已存在，直接返回路径
            if os.path.exists(output_path):
                return output_path
            
            # 设置下载选项
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(self.download_path, f"{video_id}.%(ext)s"),
            }
            
            # 下载音频
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
            
            return output_path
            
        except Exception as e:
            raise Exception(f"下载音频时出错: {str(e)}") 