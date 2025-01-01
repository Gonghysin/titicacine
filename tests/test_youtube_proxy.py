import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.utils.youtube_helper import YouTubeHelper

def test_proxy():
    # 使用代理
    proxy = "http://127.0.0.1:7897"
    yt_helper = YouTubeHelper(proxy=proxy)
    
    # 测试一个较短的视频
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    
    print("\n=== 开始下载测试 ===")
    video_path = yt_helper.download_video(test_url)
    
    if video_path and os.path.exists(video_path):
        print(f"\n✅ 测试成功!")
        print(f"文件已保存: {video_path}")
        print(f"文件大小: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
    else:
        print("\n❌ 测试失败!")

if __name__ == "__main__":
    test_proxy() 