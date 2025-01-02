import re
import os
import json
from typing import Dict, Any, List, Optional, Callable
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.nlp.v20190408 import nlp_client, models
from youtube_search import YoutubeSearch
from yt_dlp import YoutubeDL
import requests
import time

class WorkflowProcessor:
    def __init__(self, progress_callback: Optional[Callable[[float, str], None]] = None):
        """初始化工作流处理器"""
        self.progress_callback = progress_callback or self._default_progress_callback
        
        # 初始化腾讯云客户端
        print("初始化腾讯云客户端...")
        self.cred = credential.Credential(
            os.getenv("TENCENT_SECRET_ID"),
            os.getenv("TENCENT_SECRET_KEY")
        )
        http_profile = HttpProfile()
        http_profile.endpoint = "nlp.tencentcloudapi.com"
        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile
        self.client = nlp_client.NlpClient(self.cred, "ap-guangzhou", client_profile)
        
        print("初始化完成！")

    def _default_progress_callback(self, progress: float, message: str):
        """默认的进度回调函数"""
        progress_bar = "=" * int(progress * 20) + ">" + " " * (19 - int(progress * 20))
        print(f"\r[{progress_bar}] {progress*100:.1f}% - {message}", end="", flush=True)
        if progress >= 1:
            print()  # 完成时换行

    def analyze_user_requirement(self, topic: str) -> List[str]:
        """分析用户需求，使用腾讯云 NLP 服务生成关键词"""
        try:
            print(f"开始分析主题: {topic}")
            print("使用腾讯云 NLP 服务生成关键词...")
            
            # 调用腾讯云 NLP 服务的关键词提取接口
            req = models.KeywordsExtractionRequest()
            req.Text = topic
            req.Num = 5
            resp = self.client.KeywordsExtraction(req)
            
            keywords = [item.Word for item in resp.Keywords]
            print(f"生成了 {len(keywords)} 个关键词")
            return keywords
            
        except Exception as e:
            print(f"分析用户需求时出错: {str(e)}")
            raise Exception(f"分析用户需求时出错: {str(e)}")

    def select_best_video(self, videos: List[Dict[str, Any]], topic: str) -> Optional[Dict[str, Any]]:
        """从搜索结果中选择最佳视频"""
        try:
            print("使用腾讯云 NLP 服务评分视频...")
            best_score = -1
            best_video = None
            
            for video in videos:
                # 使用腾讯云 NLP 服务的文本相似度接口
                req = models.TextSimilarityRequest()
                req.SrcText = topic
                req.TargetText = f"{video['title']}\n{video.get('description', '')}"
                resp = self.client.TextSimilarity(req)
                
                score = resp.Similarity
                if score > best_score:
                    best_score = score
                    best_video = video
            
            return best_video
            
        except Exception as e:
            raise Exception(f"选择视频时出错: {str(e)}")

    def generate_article(self, video_info: Dict[str, Any], transcript: str) -> str:
        """生成文章，使用腾讯云 NLP 服务"""
        try:
            # 预处理转录文本
            print("预处理转录文本...")
            processed_transcript = self.preprocess_transcript(transcript)
            
            # 使用腾讯云 NLP 服务的文本摘要接口
            print("生成文章摘要...")
            req = models.AutoSummarizationRequest()
            req.Text = processed_transcript
            req.Length = 300
            resp = self.client.AutoSummarization(req)
            
            summary = resp.Summary
            
            # 构建文章结构
            article = f"""# {video_info.get('title', '')}

## 视频概要
{summary}

## 主要内容
{processed_transcript}

## 总结
本文基于视频内容，详细介绍了相关主题。希望这些内容对您有所帮助。
"""
            
            return article
            
        except Exception as e:
            print(f"生成文章时出错: {str(e)}")
            return None

    def validate_article(self, article: str) -> Dict[str, Any]:
        """验证生成的文章是否符合要求"""
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
            
            # 检查字数是否在合理范围内
            if word_count < 1000 or word_count > 1500:
                return {
                    "is_valid": False,
                    "reason": f"文章字数（{word_count}字）不在1000-1500字范围内"
                }
            
            # 检查标题格式
            if not re.search(r'^# .+', article, re.MULTILINE):
                return {
                    "is_valid": False,
                    "reason": "缺少一级标题"
                }
            
            # 检查二级标题数量
            h2_titles = re.findall(r'^## .+', article, re.MULTILINE)
            if len(h2_titles) < 2 or len(h2_titles) > 3:
                return {
                    "is_valid": False,
                    "reason": f"二级标题数量（{len(h2_titles)}个）不在2-3个范围内"
                }
            
            return {
                "is_valid": True,
                "word_count": word_count,
                "h2_count": len(h2_titles)
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "reason": f"验证文章时出错: {str(e)}"
            }

    def preprocess_transcript(self, transcript: str) -> str:
        """预处理转录文本"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', transcript).strip()
        
        # 移除时间戳
        text = re.sub(r'\[\d+:\d+\]', '', text)
        
        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?，。！？]', '', text)
        
        return text 