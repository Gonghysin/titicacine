import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Union
from datetime import datetime
from pathlib import Path

class XiaoAI:
    def __init__(self, api_key: str = None, max_history: int = 10, system_prompt: str = "You are a helpful assistant."):
        """
        初始化XiaoAI实例
        
        Args:
            api_key (str, optional): API密钥。如果不提供，将尝试从环境变量获取
            max_history (int): 保留的最大对话轮数（不包括system消息）
            system_prompt (str): 系统提示词
        """
        # 获取 API key
        self.api_key = api_key or os.getenv('XIAOAI_API_KEY') or 'sk-c7vyPJD9SMQ7aweJQIJC79pr9OOQhggBgQ82JyXQ0CZGWjtp'
            
        self.client = OpenAI(
            base_url='https://xiaoai.plus/v1',
            api_key=self.api_key
        )
        self.max_history = max_history
        self.default_system_prompt = system_prompt
        self.chat_history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]
        self.full_history: List[Dict[str, str]] = []
    
    def chat(self, message: str, system_prompt: str = None) -> str:
        """
        与AI进行对话，并保持对话历史记录
        
        Args:
            message (str): 用户输入的消息
            system_prompt (str, optional): 临时的系统提示词，如果不提供则使用默认值
            
        Returns:
            str: AI的回复内容
        """
        # 如果提供了新的system_prompt，临时更新它
        current_system_prompt = system_prompt or self.chat_history[0]["content"]
        messages = [{"role": "system", "content": current_system_prompt}] + self.chat_history[1:]
        
        # 添加用户消息到历史记录
        current_message = {"role": "user", "content": message}
        messages.append(current_message)
        self.chat_history.append(current_message)
        self.full_history.append({**current_message, "timestamp": datetime.now().isoformat()})
        
        try:
            # 发送请求到API
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages  # 使用可能包含临时system_prompt的消息列表
            )
            
            # 获取AI回复
            ai_response = completion.choices[0].message.content
            
            # 更新历史记录
            ai_message = {"role": "assistant", "content": ai_response}
            self.chat_history.append(ai_message)
            self.full_history.append({**ai_message, "timestamp": datetime.now().isoformat()})
            
            # 保持历史记录在指定长度内
            while len(self.chat_history) > self.max_history + 1:  # +1 是因为要保留system消息
                self.chat_history.pop(1)  # 移除最早的消息，但保留system消息
            
            return ai_response
            
        except Exception as e:
            return f"发生错误: {str(e)}"
    
    def clear_history(self):
        """清除对话历史记录，只保留system消息"""
        self.chat_history = [
            {"role": "system", "content": self.default_system_prompt}
        ]
        self.full_history = []
    
    def get_full_history(self) -> List[Dict[str, str]]:
        """获取完整的对话历史记录"""
        return self.full_history
    
    def set_max_history(self, max_history: int):
        """设置保留的最大对话轮数"""
        self.max_history = max_history
        while len(self.chat_history) > max_history + 1:
            self.chat_history.pop(1)
    
    def set_system_prompt(self, system_prompt: str):
        """更新默认系统提示词"""
        self.default_system_prompt = system_prompt
        self.chat_history[0]["content"] = system_prompt

    def transcribe_audio(self, 
                        audio_path: Union[str, Path], 
                        language: str = "zh", 
                        save_result: bool = False, 
                        output_path: str = None) -> str:
        """
        将音频文件转换为文字

        Args:
            audio_path (Union[str, Path]): 音频文件路径
            language (str, optional): 音频语言，默认"zh"(中文)。支持的语言代码：
                - 'zh': 中文
                - 'en': 英文
                - 'ja': 日语
                - 'ko': 韩语
                - 'auto': 自动检测
            save_result (bool, optional): 是否保存转录结果到文件
            output_path (str, optional): 保存结果的文件路径，如果不提供则使用默认路径

        Returns:
            str: 转录的文本内容

        Raises:
            FileNotFoundError: 音频文件不存在
            ValueError: 不支持的音频格式或语言代码
        """
        # 支持的语言代码
        supported_languages = {
            'zh': 'Chinese',
            'en': 'English',
            'ja': 'Japanese',
            'ko': 'Korean',
            'auto': None  # 自动检测
        }

        # 检查语言代码
        if language not in supported_languages:
            raise ValueError(f"不支持的语言代码: {language}. 支持的语言代码: {', '.join(supported_languages.keys())}")

        # 转换为Path对象
        audio_path = Path(audio_path)

        # 检查文件是否存在
        if not audio_path.exists():
            raise FileNotFoundError(f"找不到音频文件: {audio_path}")

        # 检查文件格式
        allowed_formats = {'.wav', '.mp3', '.m4a'}
        if audio_path.suffix.lower() not in allowed_formats:
            raise ValueError(f"不支持的音频格式: {audio_path.suffix}. 支持的格式: {', '.join(allowed_formats)}")

        try:
            # 打开音频文件
            with open(audio_path, "rb") as audio_file:
                # 调用Whisper API进行转录
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    language=language if language != 'auto' else None
                )

            # 如果需要保存结果
            if save_result:
                # 确定输出路径
                if output_path is None:
                    output_path = audio_path.with_suffix('.txt')
                
                # 保存转录结果
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(transcript)

            return transcript

        except Exception as e:
            raise Exception(f"音频转录失败: {str(e)}")

# 创建默认实例，方便直接调用
default_ai = XiaoAI(system_prompt="你是一个专业的Python编程助手，你需要记住用户的信息和对话内容。")
chat = default_ai.chat
clear_history = default_ai.clear_history
get_full_history = default_ai.get_full_history
set_max_history = default_ai.set_max_history
set_system_prompt = default_ai.set_system_prompt
transcribe_audio = default_ai.transcribe_audio  # 导出新函数
