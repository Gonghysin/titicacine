import re
import os
import json
from openai import OpenAI
from typing import Dict, Any, List, Optional, Callable
from youtube_search import YoutubeSearch
from yt_dlp import YoutubeDL
import requests
from utils.deepseek_helper import DeepseekHelper
from utils.openai_helper import OpenAIHelper
import time

class WorkflowProcessor:
    def __init__(self, progress_callback: Optional[Callable[[float, str], None]] = None):
        """初始化工作流处理器"""
        self.progress_callback = progress_callback or self._default_progress_callback
        
        # 初始化 OpenAI 和 DeepSeek 助手
        print("初始化 OpenAIHelper...")
        self.openai_helper = OpenAIHelper()
        self.deepseek_helper = DeepseekHelper()
        
        print("初始化完成！")

    def _default_progress_callback(self, progress: float, message: str):
        """默认的进度回调函数"""
        progress_bar = "=" * int(progress * 20) + ">" + " " * (19 - int(progress * 20))
        print(f"\r[{progress_bar}] {progress*100:.1f}% - {message}", end="", flush=True)
        if progress >= 1:
            print()  # 完成时换行

    def analyze_user_requirement(self, topic: str) -> List[str]:
        """分析用户需求，使用 DeepSeek 模型生成搜索关键词"""
        try:
            print(f"开始分析主题: {topic}")
            print("使用 DeepSeek 模型生成关键词...")
            
            keywords = self.deepseek_helper.analyze_topic(topic)
            print(f"生成了 {len(keywords)} 个关键词")
            return keywords
            
        except Exception as e:
            print(f"分析用户需求时出错: {str(e)}")
            raise Exception(f"分析用户需求时出错: {str(e)}")

    def select_best_video(self, videos: List[Dict[str, Any]], topic: str) -> Optional[Dict[str, Any]]:
        """从搜索结果中选择最佳视频"""
        try:
            print("使用 DeepSeek 模型评分视频...")
            best_score = -1
            best_video = None
            
            for video in videos:
                score = self.deepseek_helper.score_content(topic, f"{video['title']}\n{video.get('description', '')}")
                if score > best_score:
                    best_score = score
                    best_video = video
            
            return best_video
            
        except Exception as e:
            raise Exception(f"选择视频时出错: {str(e)}")

    def generate_article(self, video_info: Dict[str, Any], transcript: str) -> str:
        """生成文章，使用 OpenAI API"""
        try:
            # 预处理转录文本
            print("预处理转录文本...")
            processed_transcript = self.preprocess_transcript(transcript)
            
            # 生成文章大纲
            print("生成文章大纲...")
            outline = self.generate_outline(video_info, processed_transcript)
            if not outline:
                raise Exception("生成大纲失败")
            
            # 构建提示词
            prompt = f"""
            请根据以下信息生成一篇中文公众号文章。

            视频标题: {video_info.get('title', '')}
            视频描述: {video_info.get('description', '')}
            视频时长: {video_info.get('duration', '')}秒
            
            文章大纲:
            {outline}
            
            关键信息：
            {processed_transcript}
            
            要求：
            1. 标题要求（最重要，必须严格遵守）：
               - 必须有且仅有一个一级标题（# 标题）
               - 必须有2-3个二级标题（## 小标题）
               - 一级标题必须放在文章最开头
               - 不允许使用三级及以下标题
               - 标题要简洁有力，与内容相关
            
            2. 格式要求（必须严格遵守）：
               - 必须对关键概念和重要观点使用加粗（**文字**）
               - 每个主要段落至少有一处加粗
               - 段落之间必须有空行
               - 总段落数不少于10个
               - 严格遵守markdown格式
            
            3. 字数要求（必须严格遵守）：
               - 总字数必须在1000-1500字之间
               - 每个段落建议在60-80字之间
               - 包括标题在内的所有中文字符都计入总字数
               - 每个段落必须是完整的句子
               - 如果内容不足，可以适当展开论述
               - 如果内容过多，可以适当精简
            
            4. 内容要求：
               - 主题集中，不要发散
               - 观点明确，论述清晰
               - 语言流畅自然
               - 避免重复内容
               - 每个段落要完整表达一个观点
            
            5. 语言要求：
               - 保持专业性和可读性
               - 使用流畅的中文表达
               - 避免生硬的翻译腔
               - 确保每个句子都通顺易懂
               - 保持语气的一致性
            
            请生成文章：
            """
            
            # 使用 OpenAI API 生成文章
            print("使用 OpenAI API 生成文章...")
            client = OpenAI()
            
            # 最多尝试3次生成合适长度的文章
            last_article = None
            for attempt in range(3):
                response = client.chat.completions.create(
                    model="gpt-4-1106-preview",
                    messages=[
                        {"role": "system", "content": """你是一个专业的文章写手，擅长将视频内容转换为公众号文章。你有以下特点：

1. 字数控制能力极强（最重要）：
   - 你总是确保文章总字数在1000-1500字之间，这是硬性要求
   - 你会在写作时实时计算字数，包括标题和标点符号
   - 如果发现字数即将超过1500字，你会立即停止写作并重新开始
   - 如果发现字数不足1000字，你会适当扩充内容
   - 你会通过以下方式控制字数：
     * 使用简洁的表达方式
     * 删除重复的内容
     * 合并相似的观点
     * 只保留最重要的信息

2. 标题格式严格（同样重要）：
   - 必须有且仅有一个一级标题（# 标题）
   - 必须有2-3个二级标题（## 小标题）
   - 一级标题必须放在文章最开头
   - 不允许使用三级及以下标题
   - 标题要简洁有力，与内容相关

3. 段落格式规范：
   - 每个段落60-80字
   - 段落之间必须有空行
   - 每个段落表达一个完整观点
   - 总段落数不少于10个
   - 适当使用加粗标记（**关键词**）

4. 内容质量把控：
   - 主题集中，不偏离主题
   - 观点明确，论述有力
   - 语言流畅自然
   - 避免内容重复
   - 适当使用数据和例子"""},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                
                article = response.choices[0].message.content
                if not article or len(article.strip()) < 10:  # 如果生成的文章为空或太短
                    print(f"第{attempt + 1}次尝试生成的文章无效，重新生成...")
                    continue
                
                # 验证字数
                chinese_chars = re.findall(r'[\u4e00-\u9fff]', article)
                word_count = len(chinese_chars)
                last_article = article  # 保存最后一次有效的生成结果
                
                if 1000 <= word_count <= 1500:
                    print("文章字数符合要求")
                    return article
                    
                print(f"第{attempt + 1}次尝试生成的文章字数不符合要求（{word_count}字），重新生成...")
                
                # 添加字数控制提示
                if word_count < 1000:
                    prompt += f"""
                    生成的文章字数不足（{word_count}字），请按照以下要求重新生成：
                    1. 总字数必须在1000-1500字之间
                    2. 可以通过以下方式扩充内容：
                       - 添加具体的例子
                       - 展开重要观点
                       - 补充相关数据
                    3. 保持原有的结构和主要观点
                    4. 确保内容质量不降低
                    """
                else:
                    prompt += f"""
                    生成的文章字数过多（{word_count}字），请按照以下要求重新生成：
                    1. 总字数必须在1000-1500字之间
                    2. 可以通过以下方式精简内容：
                       - 删除次要信息
                       - 合并相似内容
                       - 使用更简洁的表达
                    3. 保持原有的结构和主要观点
                    4. 确保内容质量不降低
                    """
            
            # 如果3次尝试都失败，返回最后一次有效的生成结果
            # 如果没有有效结果，则重新生成一篇基础文章
            if not last_article:
                print("所有尝试都失败，生成一篇基础文章...")
                base_prompt = f"""
                请生成一篇关于"{video_info.get('title', '')}"的基础文章，要求：
                1. 字数严格控制在1000-1500字之间
                2. 必须有且仅有一个一级标题（# 标题）
                3. 必须有2-3个二级标题（## 小标题）
                4. 每个段落要有加粗关键词
                5. 总段落数不少于10个
                6. 内容要有实质性
                """
                response = client.chat.completions.create(
                    model="gpt-4-1106-preview",
                    messages=[
                        {"role": "system", "content": "你是一个专业的文章写手，擅长生成基础文章。你总是严格控制文章字数在1000-1500字之间。"},
                        {"role": "user", "content": base_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                last_article = response.choices[0].message.content
            
            return last_article
            
        except Exception as e:
            print(f"生成文章时出错: {str(e)}")
            return None

    def validate_article(self, article: str) -> Dict[str, Any]:
        """验证生成的文章是否符合要求，如果不符合则使用 DeepSeek 模型修复"""
        try:
            # 检查文章是否为空
            if not article:
                return {
                    "is_valid": False,
                    "reason": "文章内容为空"
                }
            
            # 计算中文字数
            chinese_chars = re.findall(r'[\u4e00-\u9fff]', article)
            word_count = len(chinese_chars)
            
            # 检查格式要求
            format_issues = []
            
            # 检查一级标题
            h1_matches = re.findall(r'#\s+[^\n]+', article)
            if not h1_matches:
                format_issues.append("缺少一级标题")
            elif len(h1_matches) > 1:
                format_issues.append("一级标题多于一个")
                
            # 检查二级标题
            h2_matches = re.findall(r'##\s+[^\n]+', article)
            if not h2_matches:
                format_issues.append("缺少二级标题")
            elif len(h2_matches) < 2:
                format_issues.append("二级标题少于两个")
                
            # 检查加粗文字
            bold_matches = re.findall(r'\*\*[^*\n]+\*\*', article)
            if not bold_matches:
                format_issues.append("缺少加粗文字")
            elif len(bold_matches) < 3:
                format_issues.append("加粗文字使用太少")
                
            # 检查段落间空行
            paragraphs = article.split('\n\n')
            if len(paragraphs) < 10:
                format_issues.append("段落数量不足10个")
            
            # 如果有格式问题，使用 DeepSeek 修复
            if format_issues:
                print(f"发现格式问题：{', '.join(format_issues)}")
                print("使用 DeepSeek 修复格式...")
                
                # 如果存在标题问题，先修复标题
                if any(issue for issue in format_issues if "标题" in issue):
                    print("优先修复标题问题...")
                    title_prompt = f"""
                    请修复这篇文章的标题格式，要求：
                    1. 必须有且仅有一个一级标题（# 标题）
                    2. 一级标题必须放在文章最开头
                    3. 必须有2-3个二级标题（## 小标题）
                    4. 不允许使用三级及以下标题
                    5. 标题要简洁有力，与内容相关
                    6. 不要改变文章的主要内容
                    7. 确保修改后的文章仍然通顺
                    
                    当前存在的问题：
                    {', '.join(issue for issue in format_issues if "标题" in issue)}
                    
                    需要修改的文章：
                    {article}
                    
                    请直接返回修改后的文章，不要包含任何解释："""
                    
                    # 最多尝试3次修复标题
                    for attempt in range(3):
                        article = self.deepseek_helper.review_article(article, title_prompt)
                        
                        # 重新检查标题问题
                        title_issues = []
                        
                        # 检查一级标题
                        h1_matches = re.findall(r'#\s+[^\n]+', article)
                        if not h1_matches:
                            title_issues.append("缺少一级标题")
                        elif len(h1_matches) > 1:
                            title_issues.append("一级标题多于一个")
                        elif not article.strip().startswith('#'):
                            title_issues.append("一级标题未放在文章开头")
                            
                        # 检查二级标题
                        h2_matches = re.findall(r'##\s+[^\n]+', article)
                        if not h2_matches:
                            title_issues.append("缺少二级标题")
                        elif len(h2_matches) < 2:
                            title_issues.append("二级标题少于两个")
                        elif len(h2_matches) > 3:
                            title_issues.append("二级标题多于三个")
                            
                        # 检查是否有三级及以下标题
                        h3_matches = re.findall(r'###\s+[^\n]+', article)
                        if h3_matches:
                            title_issues.append("存在三级及以下标题")
                        
                        if not title_issues:
                            print("标题问题已修复")
                            break
                        else:
                            print(f"第{attempt + 1}次修复后仍存在标题问题：{', '.join(title_issues)}")
                            
                            # 根据具体问题调整提示词
                            if "一级标题多于一个" in title_issues:
                                title_prompt = f"""
                                请严格按照以下步骤修复文章的标题：
                                1. 找出所有一级标题（以单个#开头的标题）
                                2. 保留第一个一级标题，将其他一级标题改为二级标题（##）
                                3. 确保一级标题在文章最开头
                                4. 确保总共有2-3个二级标题
                                5. 删除所有三级及以下标题
                                6. 不要改变标题的内容，只修改标题的级别
                                
                                当前文章：
                                {article}
                                
                                请直接返回修改后的文章："""
                    
                    # 如果标题问题已解决或不存在标题问题，处理其他格式问题
                    format_prompt = f"""
                    请修复这篇文章的格式问题，要求：
                    
                    1. 加粗要求：
                       - 必须对关键概念和重要观点使用加粗（**文字**）
                       - 每个主要段落至少有一处加粗
                       - 加粗要突出重点，不要过度使用
                    
                    2. 段落要求：
                       - 段落之间必须有空行
                       - 每个段落要完整表达一个观点
                       - 总段落数不少于10个
                    
                    3. 注意事项：
                       - 保持原文的表达方式和文风
                       - 不要改变文章的主要内容
                       - 确保修改后的文章仍然通顺
                       - 确保字数在1000-1500字之间
                    
                    当前存在的问题：
                    {', '.join(issue for issue in format_issues if "标题" not in issue)}
                    
                    需要修改的文章：
                    {article}
                    
                    请直接返回修改后的文章，不要包含任何解释："""
                    
                    # 最多尝试3次修复其他格式问题
                    for attempt in range(3):
                        article = self.deepseek_helper.review_article(article, format_prompt)
                        
                        # 重新检查格式问题
                        format_issues = []
                        
                        # 检查加粗文字
                        bold_matches = re.findall(r'\*\*[^*\n]+\*\*', article)
                        if not bold_matches:
                            format_issues.append("缺少加粗文字")
                        elif len(bold_matches) < 3:
                            format_issues.append("加粗文字使用太少")
                            
                        # 检查段落间空行
                        paragraphs = article.split('\n\n')
                        if len(paragraphs) < 10:
                            format_issues.append("段落数量不足10个")
                        
                        if not format_issues:
                            print("格式问题已修复")
                            break
                        else:
                            print(f"第{attempt + 1}次修复后仍存在问题：{', '.join(format_issues)}")
            
            # 如果仍有格式问题，返回验证失败
            if format_issues:
                return {
                    "is_valid": False,
                    "reason": f"格式问题：{', '.join(format_issues)}"
                }
            
            # 再次检查字数
            if word_count < 1000:
                return {
                    "is_valid": False,
                    "reason": f"文章字数不足，当前字数：{word_count}"
                }
            elif word_count > 2000:
                return {
                    "is_valid": False,
                    "reason": f"文章字数超出限制，当前字数：{word_count}"
                }
            
            # 所有检查都通过
            return {
                "is_valid": True,
                "word_count": word_count,
                "paragraph_count": len(paragraphs),
                "article": article
            }
            
        except Exception as e:
            print(f"验证文章时出错: {str(e)}")
            return {
                "is_valid": False,
                "reason": f"验证文章时出错: {str(e)}"
            }

    def search_videos(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索相关视频"""
        try:
            results = YoutubeSearch(keyword, max_results=3).to_dict()
            videos = []
            for video in results:
                videos.append({
                    "id": video["id"],
                    "title": video["title"],
                    "description": video.get("long_desc", ""),
                    "duration": video.get("duration", ""),
                    "url": f"https://www.youtube.com/watch?v={video['id']}"
                })
            return videos
        except Exception as e:
            print(f"搜索视频时出错: {str(e)}")
            return []

    def download_video(self, video_url: str) -> Optional[str]:
        """下载视频并转换为音频"""
        try:
            # 配置下载选项
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': 'downloads/%(id)s.%(ext)s',
            }
            
            # 确保下载目录存在
            os.makedirs('downloads', exist_ok=True)
            
            # 下载视频
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                audio_path = f"downloads/{info['id']}.mp3"
                return audio_path if os.path.exists(audio_path) else None
                
        except Exception as e:
            print(f"下载视频时出错: {str(e)}")
            return None 

    def compress_audio(self, input_path: str, max_size_mb: int = 24) -> Optional[str]:
        """压缩音频文件到指定大小"""
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                print(f"输入文件不存在: {input_path}")
                return None
                
            # 生成压缩后的文件路径
            output_path = input_path.replace(".mp3", "_compressed.mp3")
            
            # 获取输入文件大小（MB）
            input_size = os.path.getsize(input_path) / (1024 * 1024)
            
            if input_size <= max_size_mb:
                print(f"文件大小已经在限制范围内: {input_size:.2f}MB")
                return input_path
                
            # 计算需要的比特率
            duration = float(os.popen(f'ffprobe -i "{input_path}" -show_entries format=duration -v quiet -of csv="p=0"').read().strip())
            target_bitrate = int((max_size_mb * 8 * 1024 * 1024) / duration)
            
            # 使用 ffmpeg 压缩音频
            cmd = f'ffmpeg -y -i "{input_path}" -b:a {target_bitrate} "{output_path}"'
            os.system(cmd)
            
            if os.path.exists(output_path):
                print(f"音频压缩完成: {os.path.getsize(output_path) / (1024 * 1024):.2f}MB")
                # 删除原文件
                os.remove(input_path)
                return output_path
            else:
                print("音频压缩失败")
                return None
                
        except Exception as e:
            print(f"压缩音频时出错: {str(e)}")
            return None

    def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """转录音频文件"""
        try:
            # 压缩音频文件
            print("压缩音频文件...")
            compressed_path = self.compress_audio(audio_path)
            if not compressed_path:
                raise Exception("音频压缩失败")
            
            # 使用 OpenAI Whisper API 转录音频
            whisper_model = "whisper-1"
            print(f"\n=== 使用 OpenAI API {whisper_model} 模型转录音频 ===")
            
            with open(compressed_path, "rb") as audio_file:
                transcript = self.openai_helper.client.audio.transcriptions.create(
                    model=whisper_model,
                    file=audio_file,
                    response_format="text"
                )
            
            # 删除压缩后的音频文件
            if compressed_path != audio_path and os.path.exists(compressed_path):
                os.remove(compressed_path)
                
            return transcript
            
        except Exception as e:
            print(f"转录音频时出错: {str(e)}")
            return None

    def save_article(self, article: str, video_info: Dict[str, Any]) -> str:
        """保存文章到本地"""
        try:
            # 确保目录存在
            save_dir = os.path.join("data", "articles")
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成文件名（使用时间戳和视频标题）
            timestamp = int(time.time())
            title = video_info.get("title", "untitled").replace(" ", "_")[:50]  # 限制长度
            filename = f"{timestamp}_{title}.md"
            filepath = os.path.join(save_dir, filename)
            
            # 保存文章
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(article)
            
            print(f"文章已保存: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"保存文章时出错: {str(e)}")
            return ""

    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            # 清理 downloads 目录
            if os.path.exists("downloads"):
                for file in os.listdir("downloads"):
                    try:
                        file_path = os.path.join("downloads", file)
                        os.remove(file_path)
                        print(f"已删除临时文件: {file_path}")
                    except Exception as e:
                        print(f"删除文件 {file} 时出错: {str(e)}")
                
                # 尝试删除空目录
                try:
                    os.rmdir("downloads")
                    print("已删除 downloads 目录")
                except:
                    pass
            
        except Exception as e:
            print(f"清理临时文件时出错: {str(e)}")

    def process_workflow(self, topic: str, mode: str = "1") -> Dict[str, Any]:
        """处理工作流程"""
        try:
            print(f"\n开始处理主题: {topic}")
            print(f"处理模式: {mode}")
            
            # 更新进度：10%
            if self.progress_callback:
                self.progress_callback(0.1, "正在分析用户需求...")
            print("\n[步骤1] 正在分析用户需求，生成搜索关键词...")
            
            # 分析用户需求，生成搜索关键词
            keywords = self.analyze_user_requirement(topic)
            if not keywords:
                print("生成关键词失败")
                return {"error": "生成关键词失败"}
            print(f"成功生成关键词: {keywords}")
            
            # 更新进度：20%
            if self.progress_callback:
                self.progress_callback(0.2, "正在搜索相关视频...")
            print("\n[步骤2] 正在搜索相关视频...")
            
            # 搜索相关视频
            videos = []
            for i, keyword in enumerate(keywords, 1):
                print(f"搜索第{i}个关键词: {keyword}")
                results = self.search_videos(keyword)
                videos.extend(results)
                print(f"找到 {len(results)} 个相关视频")
            
            if not videos:
                print("未找到相关视频")
                return {"error": "未找到相关视频"}
            print(f"总共找到 {len(videos)} 个相关视频")
            
            # 更新进度：30%
            if self.progress_callback:
                self.progress_callback(0.3, "正在选择最佳视频...")
            print("\n[步骤3] 正在选择最佳视频...")
            
            # 选择最佳视频
            video = self.select_best_video(videos, topic)
            if not video:
                print("选择视频失败")
                return {"error": "选择视频失败"}
            print(f"选中视频: {video.get('title', '')}")
            print(f"视频URL: {video.get('url', '')}")
            
            if mode == "1":
                # 更新进度：40%
                if self.progress_callback:
                    self.progress_callback(0.4, "正在下载视频...")
                print("\n[步骤4] 正在下载视频...")
                
                # 下载视频音频
                print(f"开始下载视频: {video.get('url', '')}")
                audio_path = self.download_video(video["url"])
                if not audio_path:
                    print("下载视频失败")
                    return {"error": "下载视频失败"}
                print(f"视频下载完成，保存为: {audio_path}")
                
                # 更新进度：60%
                if self.progress_callback:
                    self.progress_callback(0.6, "正在转录音频...")
                print("\n[步骤5] 正在转录音频...")
                
                # 转录音频
                print("使用 Whisper 模型转录音频...")
                transcript = self.transcribe_audio(audio_path)
                if not transcript:
                    print("转录音频失败")
                    return {"error": "转录音频失败"}
                print("音频转录完成")
                print(f"转录文本长度: {len(transcript)} 字符")
                
                # 清理临时文件
                try:
                    os.remove(audio_path)
                    print("临时文件清理完成")
                except:
                    print("清理临时文件失败")
                    pass
            else:
                transcript = ""
                print("\n[跳过步骤4和5] 使用模式2，不下载和转录视频")
            
            # 更新进度：80%
            if self.progress_callback:
                self.progress_callback(0.8, "正在生成文章...")
            print("\n[步骤6] 正在生成文章...")
            
            # 生成文章
            article = self.generate_article(video, transcript)
            if not article:
                print("文章生成失败")
                return {"error": "文章生成失败"}
            print("文章生成完成")
            print(f"文章长度: {len(article)} 字符")
            
            # 更新进度：90%
            if self.progress_callback:
                self.progress_callback(0.9, "正在验证文章...")
            print("\n[步骤7] 正在验证文章...")
            
            # 验证文章
            print("开始验证文章...")
            validation_result = self.validate_article(article)
            
            # 即使验证失败，也保存文章
            saved_path = self.save_article(validation_result.get("article", article), video)
            
            # 输出验证结果
            if not validation_result.get("is_valid", False):
                print(f"文章验证失败: {validation_result.get('reason', '未知原因')}")
            else:
                print("文章验证通过")
            
            print(f"最终字数: {validation_result.get('word_count', 0)}")
            print(f"段落数量: {validation_result.get('paragraph_count', 0)}")
            
            # 清理临时文件
            self.cleanup_temp_files()
            
            # 更新进度：100%
            if self.progress_callback:
                self.progress_callback(1.0, "处理完成")
            print("\n处理完成!")
            
            # 返回结果
            return {
                "keywords": keywords,
                "video": {
                    "title": video.get("title", ""),
                    "url": video.get("url", ""),
                    "duration": video.get("duration", "")
                },
                "article": validation_result.get("article", article),
                "word_count": validation_result.get("word_count", 0),
                "saved_path": saved_path,
                "validation_result": {
                    "is_valid": validation_result.get("is_valid", False),
                    "reason": validation_result.get("reason", "未知原因")
                }
            }
            
        except Exception as e:
            print(f"\n处理过程中出现错误: {str(e)}")
            import traceback
            print("错误详情:")
            print(traceback.format_exc())
            return {"error": f"处理过程中出现错误: {str(e)}"}

    def preprocess_transcript(self, transcript: str) -> str:
        """预处理转录文本，使用 DeepSeek 模型提取关键信息"""
        try:
            model_name = "deepseek-chat"
            print(f"\n=== 使用 {model_name} 模型预处理转录文本 ===")
            prompt = f"""
            请对以下转录文本进行处理，提取最重要的信息和关键点。要求：
            1. 提取的内容必须少于500字
            2. 保留最核心、最相关的内容
            3. 去除重复和冗余的信息
            4. 使用简洁的语言概括
            
            转录文本：
            {transcript}
            
            请提取关键信息：
            """
            
            response = self.deepseek_helper.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的文本处理专家，擅长从长文本中提取关键信息。你总是使用简洁的语言，去除重复和冗余的内容。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"处理转录文本时出错: {str(e)}")
            return transcript

    def generate_outline(self, video_info: Dict[str, Any], processed_transcript: str) -> Optional[str]:
        """生成文章大纲，使用 DeepSeek 模型"""
        try:
            model_name = "deepseek-chat"
            print(f"\n=== 使用 {model_name} 模型生成文章大纲 ===")
            prompt = f"""
            请根据以下信息生成一篇中文文章的精简大纲。

            视频标题: {video_info.get('title', '')}
            视频描述: {video_info.get('description', '')}
            视频时长: {video_info.get('duration', '')}秒
            
            关键信息：
            {processed_transcript}
            
            要求：
            1. 大纲结构（必须严格遵守）：
               - 一级标题：1个，20字以内
               - 二级标题：2个，每个10字以内
               - 每个二级标题下：3个要点，每个要点30字以内
               - 开篇要点：2个，每个要点30字以内
               - 结尾要点：2个，每个要点30字以内
            
            2. 内容要求：
               - 主题集中，不要发散
               - 每个要点简洁明了
               - 避免重复内容
               - 确保内容连贯
            
            3. 格式要求：
               - 使用markdown格式
               - 使用"-"作为要点标记
               - 保持适当的缩进
               - 要点之间要有空行
            
            请生成大纲：
            """
            
            response = self.deepseek_helper.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的文章策划专家，擅长设计结构清晰、层次分明的文章大纲。你总是确保大纲的每个要点都简洁明了，避免过度展开。你会严格控制每个要点的字数，确保生成的文章不会超出预期长度。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"生成大纲时出错: {str(e)}")
            return None 