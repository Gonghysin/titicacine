import whisper

class AudioTranscriber:
    def __init__(self):
        """
        初始化音频转录器
        """
        self.model = whisper.load_model("base")
    
    def transcribe(self, audio_path: str) -> str:
        """
        转录音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            转录文本
        """
        try:
            # 加载并转录音频
            result = self.model.transcribe(audio_path)
            
            # 返回转录文本
            return result["text"]
            
        except Exception as e:
            raise Exception(f"转录音频时出错: {str(e)}") 