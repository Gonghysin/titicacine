from workflow_processor import WorkflowProcessor
import yt_dlp

def main():
    # 配置yt-dlp选项
    ydl_opts = {
        'format': 'best',  # 选择最佳质量
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        # 添加自定义headers来模拟浏览器
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        },
        'proxy': 'socks5://127.0.0.1:7897'  # 替换成你的代理地址
    }
    
    # 注入yt-dlp配置到处理器
    processor = WorkflowProcessor(ydl_opts)
    processor.run()

if __name__ == "__main__":
    main()