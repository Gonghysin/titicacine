import re
import os
import json
from openai import OpenAI
from typing import Dict, Any, List, Optional, Callable
from youtube_search import YoutubeSearch
from yt_dlp import YoutubeDL
import requests
import time

class WorkflowProcessor:
    def __init__(self, progress_callback: Optional[Callable[[float, str], None]] = None):
        """初始化工作流处理器"""
        self.progress_callback = progress_callback or self._default_progress_callback
        self.client = OpenAI()
        print("初始化完成！")

    def _default_progress_callback(self, progress: float, message: str):
        """默认的进度回调函数"""
        progress_bar = "=" * int(progress * 20) + ">" + " " * (19 - int(progress * 20))
        print(f"\r[{progress_bar}] {progress*100:.1f}% - {message}", end="", flush=True)
        if progress >= 1:
            print()  # 完成时换行

    def analyze_user_requirement(self, topic: str) -> List[str]:
        """分析用户需求，使用 OpenAI 模型生成搜索关键词"""
        try:
            print(f"开始分析主题: {topic}")
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个帮助用户分析主题并生成相关搜索关键词的助手。"},
                    {"role": "user", "content": f"请分析主题'{topic}'，生成3-5个相关的搜索关键词，每行一个关键词。"}
                ]
            )
            
            keywords = response.choices[0].message.content.strip().split('\n')
            print(f"生成了 {len(keywords)} 个关键词")
            return keywords
            
        except Exception as e:
            print(f"分析用户需求时出错: {str(e)}")
            raise Exception(f"分析用户需求时出错: {str(e)}")

    def process_workflow(self, topic: str, mode: str = "1") -> Dict[str, Any]:
        """处理整个工作流"""
        try:
            # 1. 分析用户需求，生成搜索关键词
            keywords = self.analyze_user_requirement(topic)
            self.progress_callback(0.2, "已生成搜索关键词")

            # 2. 生成文章大纲
            outline_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个帮助用户生成文章大纲的助手。"},
                    {"role": "user", "content": f"请根据主题'{topic}'和关键词{keywords}生成一个详细的文章大纲。"}
                ]
            )
            outline = outline_response.choices[0].message.content
            self.progress_callback(0.4, "已生成文章大纲")

            # 3. 生成文章内容
            content_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个帮助用户生成高质量文章的助手。"},
                    {"role": "user", "content": f"请根据主题'{topic}'和大纲'{outline}'生成一篇详细的文章。要求：\n1. 内容丰富详实\n2. 逻辑清晰\n3. 语言流畅\n4. 适合{mode=='1' and '公众号' or '博客'}平台"}
                ]
            )
            content = content_response.choices[0].message.content
            self.progress_callback(0.8, "已生成文章内容")

            # 4. 优化文章格式
            format_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个帮助用户优化文章格式的助手。"},
                    {"role": "user", "content": f"请优化以下文章的格式，使其更适合{mode=='1' and '公众号' or '博客'}平台阅读：\n\n{content}"}
                ]
            )
            formatted_content = format_response.choices[0].message.content
            self.progress_callback(1.0, "文章生成完成")

            return {
                "keywords": keywords,
                "outline": outline,
                "content": formatted_content
            }

        except Exception as e:
            print(f"处理工作流时出错: {str(e)}")
            raise Exception(f"处理工作流时出错: {str(e)}") 