import os
import json
import logging
import whisper
from typing import Optional

logger = logging.getLogger(__name__)

def transcribe_audio(audio_path: str) -> Optional[str]:
    """
    使用Whisper模型转录音频
    :param audio_path: 音频文件路径
    :return: 转录文本
    """
    try:
        logger.info(f"开始转录音频: {audio_path}")
        
        # 加载模型
        model = whisper.load_model("base")
        
        # 转录音频
        result = model.transcribe(audio_path, language="zh")
        
        return result["text"]
        
    except Exception as e:
        logger.error(f"转录音频时出错: {str(e)}")
        return None

# 使用示例
if __name__ == "__main__":
    # 调用函数转写音频
    audio_file = "BV1EE411n7cX.mp3"  # 替换为您的音频文件路径
    result = transcribe_audio(audio_file)
    
    if result:
        print("\n转写结果：")
        print(result)
        
        # 可选：保存到文件
        with open('transcription.txt', 'w', encoding='utf-8') as f:
            f.write(result)
        print("\n转写结果已保存到 transcription.txt")
    else:
        print("转写失败")


        # 在其他程序中调用此函数的方法如下：
        # 
        # from tset import transcribe_audio
        # 
        # audio_file = "path_to_your_audio_file.mp3"
        # result = transcribe_audio(audio_file)
        # 
        # if result:
        #     print("转写结果：")
        #     print(result)
        # else:
        #     print("转写失败")
        #
        # 返回值：
        # 如果转写成功，返回转写的文本内容（字符串）。
        # 如果转写失败，返回 None。
