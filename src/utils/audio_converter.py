import os
import subprocess

class AudioConverter:
    def __init__(self, input_dir="downloads", output_dir="downloads"):
        """
        初始化音频转换器
        :param input_dir: 输入文件目录
        :param output_dir: 输出文件目录
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 检查ffmpeg是否安装
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True)
        except FileNotFoundError:
            raise RuntimeError("请先安装ffmpeg")
    
    def convert_to_audio(self, video_path, output_path=None):
        """
        将视频转换为音频
        :param video_path: 视频文件路径
        :param output_path: 输出音频文件路径（可选）
        :return: 输出音频文件路径
        """
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
            # 如果没有指定输出路径，则使用默认路径
            if output_path is None:
                output_path = os.path.join(
                    self.output_dir,
                    os.path.splitext(os.path.basename(video_path))[0] + '.mp3'
                )
            
            print(f"开始转换: {os.path.basename(video_path)}")
            print(f"输出到: {output_path}")
            
            # 使用ffmpeg进行转换
            command = [
                'ffmpeg',
                '-i', video_path,  # 输入文件
                '-vn',  # 不处理视频
                '-acodec', 'libmp3lame',  # 使用mp3编码器
                '-q:a', '2',  # 音质设置（0-9，2是高质量）
                '-y',  # 覆盖已存在的文件
                output_path
            ]
            
            process = subprocess.run(
                command,
                capture_output=True,
                text=True
            )
            
            if process.returncode != 0:
                raise RuntimeError(f"转换失败: {process.stderr}")
            
            print("转换完成！")
            return output_path
            
        except Exception as e:
            print(f"转换失败: {str(e)}")
            return None
    
    def batch_convert(self, video_files):
        """
        批���转换视频文件
        :param video_files: 视频文件路径列表
        :return: 成功转换的文件列表
        """
        results = []
        for video_file in video_files:
            result = self.convert_to_audio(video_file)
            if result:
                results.append(result)
        return results 