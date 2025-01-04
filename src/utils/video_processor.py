import os
import logging
from typing import Optional, Dict, Any
import subprocess
from openai import OpenAI

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        """初始化视频处理器"""
        self.max_audio_size = 25 * 1024 * 1024  # 25MB 最大音频大小
        self.client = OpenAI()
        logger.info("初始化完成")

    async def process_video(self, bvid: str) -> Optional[str]:
        """
        处理视频：下载并提取音频
        :param bvid: B站视频BV号
        :return: 处理后的文本内容
        """
        try:
            logger.info(f"开始处理视频 {bvid}")
            
            # 1. 下载视频
            logger.info(f"开始下载视频: {bvid}")
            from src.utils.bilibili_helper import BilibiliHelper
            helper = BilibiliHelper()
            video_info = await helper.download_video(bvid)
            
            if not video_info or 'output_path' not in video_info:
                logger.error("视频下载失败")
                return None
                
            video_path = video_info['output_path']
            
            # 2. 提取音频
            audio_path = os.path.join('downloads', f"{bvid}.mp3")
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            
            # 先提取较低质量的音频以减小文件大小
            command = [
                'ffmpeg',
                '-i', video_path,
                '-q:a', '9',  # 降低音频质量
                '-map', 'a',
                '-ar', '16000',  # 降低采样率
                '-ac', '1',  # 转换为单声道
                '-y',  # 覆盖已存在的文件
                audio_path
            ]
            
            process = subprocess.run(command, capture_output=True, text=True)
            
            if process.returncode != 0:
                logger.error(f"音频提取失败: {process.stderr}")
                return None
                
            logger.info("音频提取完成")
            
            # 3. 转录音频
            logger.info(f"开始转录音频: {audio_path}")
            try:
                # 检查音频文件大小
                file_size = os.path.getsize(audio_path)
                logger.info(f"音频文件大小: {file_size / 1024 / 1024:.2f}MB")
                
                if file_size > self.max_audio_size:
                    logger.warning("音频文件过大，将进行分割处理")
                    # 分割音频文件
                    split_duration = 300  # 5分钟一段
                    command = [
                        'ffmpeg',
                        '-i', audio_path,
                        '-f', 'segment',
                        '-segment_time', str(split_duration),
                        '-c', 'copy',
                        os.path.join('downloads', f"{bvid}_%03d.mp3")
                    ]
                    subprocess.run(command, capture_output=True, text=True)
                    
                    # 处理每个分段
                    texts = []
                    for file in sorted(os.listdir('downloads')):
                        if file.startswith(f"{bvid}_") and file.endswith('.mp3'):
                            segment_path = os.path.join('downloads', file)
                            try:
                                text = self._transcribe_audio(segment_path)
                                if text:
                                    texts.append(text)
                            except Exception as e:
                                logger.error(f"转录分段音频失败: {str(e)}")
                            finally:
                                os.remove(segment_path)  # 删除分段文件
                    
                    if texts:
                        return "\n".join(texts)
                    return None
                else:
                    text = self._transcribe_audio(audio_path)
                    if text:
                        logger.info("音频转录完成")
                        return text
                    else:
                        logger.error("音频转录失败")
                        return None
            except Exception as e:
                logger.error(f"转录音频时出错: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"处理视频时出错: {str(e)}")
            return None

    def _transcribe_audio(self, audio_path: str) -> Optional[str]:
        """
        使用OpenAI API转录音频
        :param audio_path: 音频文件路径
        :return: 转录文本
        """
        try:
            # 使用OpenAI API进行转录
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    language="zh"
                )
            return transcript
                
        except Exception as e:
            logger.error(f"转录音频时出错: {str(e)}")
            return None 