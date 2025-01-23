import os
import time
from utils.youtube_helper import YouTubeHelper
from utils.openai_helper import OpenAIHelper
from utils.deepseek_helper import DeepSeekChat
import yt_dlp
from utils.xiaoai_ai import transcribe_audio, chat

class WorkflowProcessor:
    def __init__(self, ydl_opts):
        self.ydl_opts = ydl_opts
        print("初始化工作流处理器...")
        self.youtube_helper = YouTubeHelper()
        self.openai_helper = OpenAIHelper()
        
        self.deepseek = DeepSeekChat(
            system_message="你是一个专业的视频内容分析助手，擅长分析用户需求并找到最合适的视频。"
        )
        
        # 只创建必要的输出目录
        self.dirs = {
            'transcripts': 'transcripts',
            'articles': 'articles'
        }
        
        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)
    
    def run(self):
        """运行工作流程"""
        temp_files = []  # 用于跟踪临时文件
        
        try:
            # 1. 选择工作模式
            mode = self._select_mode()
            
            # 2. 询问用户需要什么视频
            while True:
                query = input("请输入您想要的视频主题: ")
                print("\n正在搜索合适的视频...")
                video_info = self._search_video(query)
                if video_info:
                    print(f"\n找到合适的视频：")
                    print(f"标题：{video_info['title']}")
                    print(f"时长：{video_info['duration']}秒")
                    print(f"观看量：{video_info['view_count']}")
                    
                    confirm = input("\n是否使用这个视频？(y/n): ").lower()
                    if confirm == 'y':
                        break
                    else:
                        print("\n让我们继续搜索...")
                else:
                    retry = input("\n未找到合适的视频，是否重试？(y/n): ").lower()
                    if retry != 'y':
                        print("程序结束")
                        return
            
            video_url = video_info['url']
            video_title = video_info['title']
            
            # 3. 下载视频
            print("\n开始下载视频...")
            video_path = self.youtube_helper.download_video(video_url)
            if not video_path:
                print("下载视频失败")
                return
            temp_files.append(video_path)
            
            # 4. 转换视频为音频
            print("\n开始转换音频...")
            audio_path = self.youtube_helper.convert_to_audio(video_path)
            if not audio_path:
                print("转换音频失败")
                self._cleanup_temp_files(temp_files)
                return
            temp_files.append(audio_path)
            
            # 5. 生成文稿
            print("\n开始生成文稿...")
            transcript = self.convert_audio_to_text(audio_path, video_title)
            if not transcript:
                print("生成文稿失败")
                self._cleanup_temp_files(temp_files)
                return
            
            # 如果是模式1.2，到这里就结束
            if mode == "2":
                print("\n文稿生成完成！")
                self._cleanup_temp_files(temp_files)
                return
            
            # 6. 生成公众号文章（模式1.1）
            print("\n开始生成公众号文章...")
            article = self._generate_article(transcript, video_title)
            if not article:
                print("生成文章失败")
                self._cleanup_temp_files(temp_files)
                return
            
            print("\n工作流程完成！")
            print(f"文稿已保存到：transcripts/文稿-{video_title}.md")
            if mode == "1":
                print(f"公众号文章已保存到：articles/公众号-{video_title}.md")
            
        except Exception as e:
            print(f"工作流程出错: {str(e)}")
        finally:
            if temp_files:  # 只有当有临时文件时才清理
                self._cleanup_temp_files(temp_files)
                print("\n已清理所有临时文件")
    
    def _select_mode(self):
        """选择工作模式"""
        while True:
            print("\n请选择工作模式：")
            print("1. 生成公众号文章模式")
            print("2. 视频文稿导出模式")
            
            mode = input("请输入模式编号 (1/2): ").strip()
            if mode in ["1", "2"]:
                return mode
            print("无效的选择，请重试。")
    
    def _search_video(self, query):
        """搜索并选择最佳视频"""
        try:
            print("\n1. 分析用户需求...")
            analysis_prompt = f"""
            请分析以下视频需求，给出搜索建议：
            1. 最佳搜索关键词（英文）
            2. 视频要求
            3. 建议时长
            4. 建议发布时间
            
            用户需求：{query}
            """
            analysis = self.deepseek.chat(analysis_prompt)
            print("分析结果：")
            print(analysis)
            
            print("\n2. 搜索YouTube视频...")
            videos = self.youtube_helper.search_videos(query)
            if not videos:
                print("未找到视频")
                return None
            
            print(f"\n找到 {len(videos)} 个视频，开始评估标题...")
            
            best_video = None
            best_score = 0
            
            for i, video in enumerate(videos, 1):
                if not video.get('url'):  # 检查 URL 是否存在
                    print(f"跳过第 {i} 个视频：缺少 URL")
                    continue
                    
                print(f"\n评估第 {i} 个视频:")
                print(f"标题: {video['title']}")
                print(f"URL: {video['url']}")  # 打印 URL 用于调试
                
                # 评估标题
                score_prompt = f"""
                请评估这个视频标题的质量（0-100分）：
                {video['title']}
                
                只返回分数，不要其他文字。
                """
                score = float(self.deepseek.chat(score_prompt) or 0)
                print(f"标题评分: {score}")
                
                if score > best_score:
                    best_score = score
                    best_video = video.copy()  # 创建副本以避免引用问题
                    print("★ 当前最佳选择")
            
            if best_video and best_video.get('url'):
                print("\n3. 最终选择:")
                print(f"标题: {best_video['title']}")
                print(f"URL: {best_video['url']}")
                print(f"评分: {best_score}")
                
                return best_video
                
            print("未找到合适的视频")
            return None
            
        except Exception as e:
            print(f"搜索视频时出错: {str(e)}")
            return None
    
    def convert_audio_to_text(self, audio_path, title):
        """使用 xiaoai 转换音频为文字，然后用 DeepSeek 优化"""
        try:
            # 1. 使用 xiaoai 转换音频为文字
            raw_transcript = transcribe_audio(audio_path, language='zh')
            if not raw_transcript:
                return None
            
            # 2. 使用 xiaoai 优化文稿
            optimization_prompt = f"""
            请优化以下文字稿，要求：
            1. 保持原意
            2. 分段清晰
            3. 标点符号准确
            4. 去除口语化表达
            5. 修正可能的转录错误
            
            
            原文：
            {raw_transcript}
            """
            
            optimized_transcript = chat(optimization_prompt)
            if not optimized_transcript:
                return raw_transcript  # 如果优化失败，返回原始文稿
            
            # 3. 保存优化后的文稿，使用新的命名规则
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            transcript_path = os.path.join(
                self.dirs['transcripts'], 
                f'文稿-{safe_title}.md'
            )
            
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(optimized_transcript)
            
            print(f"文稿已保存: {transcript_path}")
            return optimized_transcript
            
        except Exception as e:
            print(f"转换音频为文字时出错: {str(e)}")
            return None
    
    def _generate_article(self, transcript, title):
        """生成公众号文章"""
        try:
            prompt = f"""
            请将以下文字转换为一篇公众号文章，要：
            1. 标题吸引人
            2. 分段合理
            3. 语言生动
            4. 适合公众号阅读
            5. 2000-3000字

            注意：
            1. 输出格式为markdown格式
            2. 标题、段落分配合理，符合公众号格式
            3. 不同级别标题用markdown分级标题规则区分。最好用2个不同级别的标题，凸显层次感。
            4. 不要使用数字开头的分点分段，如"1.标题"这样，而是直接写上标题
            5. 适当加粗重要的句子
            
            原文：
            {transcript}
            """
            
            messages = [{"role": "user", "content": prompt}]
            article = self.openai_helper.generate_response(messages, model_key="ft-gpt4")
            
            if not article:
                return None
            
            print("\n开始审核文章...")
            reviewed_article = self.openai_helper.review_article(article)
            
            if not reviewed_article:
                print("审核失败，使用原始文章")
                reviewed_article = article
            
            # 使用新的命名规则保存文章
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            file_path = os.path.join(
                self.dirs['articles'], 
                f'公众号-{safe_title}.md'
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(reviewed_article)
            
            print(f"文章已保存: {file_path}")
            return reviewed_article
            
        except Exception as e:
            print(f"生成文章时出错: {str(e)}")
            return None
        

        
    def _cleanup_temp_files(self, files):
        """清理临时文件"""
        for file_path in files:
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"已删除临时文件: {file_path}")
            except Exception as e:
                print(f"删除文件时出错 {file_path}: {str(e)}") 
    
    def download_video(self, url):
        """下载视频的方法"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                ydl.download([url])
                return True
        except Exception as e:
            print(f"下载视频时出错: {str(e)}")
            try:
                # 备用下载方式：使用较低质量
                backup_opts = self.ydl_opts.copy()
                backup_opts['format'] = 'best[height<=720]'
                with yt_dlp.YoutubeDL(backup_opts) as ydl:
                    ydl.download([url])
                    return True
            except Exception as e2:
                print(f"备用下载方式也失败: {str(e2)}")
                return False 