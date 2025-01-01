import yt_dlp

def download_youtube_video(url, output_path='downloads'):
    """
    下载YouTube视频
    :param url: YouTube视频URL
    :param output_path: 下载文件保存路径
    """
    ydl_opts = {
        'format': 'best',  # 下载最好的质量
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',  # 输出模板
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("开始下载视频...")
            ydl.download([url])
            print("视频下载完成！")
    except Exception as e:
        print(f"下载出错: {str(e)}")

if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=B-Mx3hblLOg"
    download_youtube_video(video_url)
