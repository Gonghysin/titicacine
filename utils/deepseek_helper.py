from openai import OpenAI
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

class DeepSeekChat:
    def __init__(self, system_message="You are a helpful assistant"):
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        self.system_message = system_message
        self.conversation_history = [
            {"role": "system", "content": system_message}
        ]
    
    def chat(self, message, stream=False):
        """发送消息并获取回复"""
        self.conversation_history.append({"role": "user", "content": message})
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=self.conversation_history,
                stream=stream
            )
            
            if stream:
                # 流式输出
                collected_content = []
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        collected_content.append(content)
                        print(content, end='', flush=True)
                print()  # 换行
                full_content = ''.join(collected_content)
            else:
                # 非流式输出
                full_content = response.choices[0].message.content
            
            # 保存助手的回复到对话历史
            self.conversation_history.append({"role": "assistant", "content": full_content})
            return full_content
            
        except Exception as e:
            print(f"DeepSeek API 错误: {e}")
            return None
    
    def read_file(self, file_path):
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except Exception as e:
            print(f"文件读取错误: {e}")
            return None
    
    def analyze_document(self, file_path, question=None):
        """分析文档内容"""
        content = self.read_file(file_path)
        if content is None:
            return None
        
        prompt = f"以下是文档内容：\n\n{content}\n\n"
        if question:
            prompt += f"请回答以下问题：{question}"
        else:
            prompt += "请分析这份文档的主要内容并提供摘要。"
        
        return self.chat(prompt)
    
    def clear_history(self):
        """清除对话历史，只保留system message"""
        self.conversation_history = [
            {"role": "system", "content": self.system_message}
        ]
