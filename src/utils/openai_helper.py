import os
import time
from openai import OpenAI
from dotenv import load_dotenv

class OpenAIHelper:
    def __init__(self):
        print("初始化 OpenAIHelper...")
        # 加载环境变量
        load_dotenv()
        
        # 初始化 OpenAI 客户端 - 移除 proxies 参数
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url="https://api.openai.com/v1"
        )
        
        # 定义可用的模型
        self.available_models = {
            "ft-gpt4": {
                "name": "ft:gpt-4o-mini-2024-07-18:1234::Aj1D4Hzr",
                "description": "定制训练的 GPT-4 模型"
            },
            "gpt4o-mini": {
                "name": "gpt-4o-mini",
                "description": "标准 GPT-4o-mini 模型"
            },
            "gpt-3.5-16k": {
                "name": "gpt-3.5-turbo-16k",
                "description": "GPT-3.5 16K 上下文模型"
            }
        }
        
        # 模型特殊参数配置
        self.model_specific_params = {
            "gpt-3.5-16k": {
                "max_tokens": 4096  # 为 GPT-3.5-16k 设置更大的 token 限制
            }
        }
        
        # 直接设置默认模型为微调模型
        self._set_model_params("ft-gpt4")
        
        print("初始化完成！")
    
    def _set_model_params(self, model_key):
        """设置模型参数"""
        if model_key not in self.available_models:
            raise ValueError(f"未知的模型: {model_key}")
            
        # 基础参数
        self.model_params = {
            "model": self.available_models[model_key]["name"],
            "response_format": {"type": "text"},
            "temperature": 1,
            "max_tokens": 4096,  # 默认值
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }
        
        # 如果有特殊参数配置，则更新
        if model_key in self.model_specific_params:
            self.model_params.update(self.model_specific_params[model_key])
    
    def list_models(self):
        """列出所有可用的模型"""
        print("\n可用的模型：")
        for key, model in self.available_models.items():
            print(f"- {key}: {model['description']}")
    
    def select_model(self):
        """让用户选择模型"""
        self.list_models()
        while True:
            choice = input("\n请选择要使用的模型 (输入模型代号): ").strip()
            if choice in self.available_models:
                self._set_model_params(choice)
                print(f"已选择模型: {self.available_models[choice]['description']}")
                break
            print("无效的选择，请重试")
    
    def generate_response(self, messages, model_key=None):
        """
        生成回复
        :param messages: 消息列表
        :param model_key: 可选，指定使用的模型
        :return: 生成回复
        """
        try:
            # 如果指定了模型，临时切换
            if model_key:
                original_params = self.model_params.copy()
                self._set_model_params(model_key)
                print(f"\n=== 使用 {self.model_params['model']} 模型生成文章 ===")
            
            response = self.client.chat.completions.create(
                messages=messages,
                **self.model_params
            )
            
            # 如果临时切换了模型，恢复原来的参数
            if model_key:
                self.model_params = original_params
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"生成回复时出错: {str(e)}")
            return None
    
    def save_response(self, prompt, response, output_dir="responses"):
        """
        保存对话内容
        :param prompt: 输入的提示
        :param response: 生成的回复
        :param output_dir: 输出目录
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"response_{int(time.time())}.md"
            file_path = os.path.join(output_dir, filename)
            
            content = f"""# OpenAI 对话记录

## 提示
{prompt}

## 回复
{response}

生成时间: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"对话已保存: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"保存对话时出错: {str(e)}")
            return None 
    
    def review_article(self, article):
        """使用 GPT-3.5-16k 审核文章"""
        try:
            review_prompt = f"""
            请审核以下markdown格式的公众号文章，要求：
            1. 保持所有markdown格式标记不变，包括：
               - 一级标题(#)
               - 二级标题(##)
               - 加粗标记(**)
            2. 只修正明显不合逻辑或不通顺的句子
            3. 保持原有的文风和表达方式
            4. 不要改变任何正常的内容
            5. 不要修改文章结构
            6. 不要删除或更改任何格式标记
            7. 输出为markdown 而不是 html
            8. &rdquo 输出为 “
            9. &ldquo 输出为 ”
            
            如果发现格式标记缺失，请补充：
            1. 确保文章有一级标题
            2. 确保有适当的二级标题
            3. 确保重要内容有加粗标记
            
            原文：
            {article}
            
            请直接返回审核后的文章，不要包含任何解释或说明。
            """
            
            # 使用 GPT-3.5-16k 进行审核
            messages = [{"role": "user", "content": review_prompt}]
            return self.generate_response(messages, model_key="gpt-3.5-16k")
            
        except Exception as e:
            print(f"审核文章时出错: {str(e)}")
            return None 