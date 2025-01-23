import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import sys
from typing import Union, Optional, List  # 添加 typing 导入

# 添加项目根目录到 Python 路径
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.xiaoai_ai import chat

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
            "max_tokens": 2048,  # 默认值
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
        """使用 xiaoai 审核文章"""  

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
            8. &rdquo 输出为 "
            9. &ldquo 输出为 "
            
            如果发现格式标记缺失，请补充：
            1. 确保文章有一级标题
            2. 确保有适当的二级标题
            3. 确保重要内容有加粗标记
            
            原文：
            {article}
            
            请直接返回审核后的文章，不要包含任何解释或说明。
            """
            
        return chat(review_prompt)

    def add_bold_marks(self, article):
        """为文章添加加粗标记"""
        bold_prompt = f"""
        请为以下文章添加加粗标记(**), 要求：
        1. 只给重要的关键词、核心概念添加加粗
        2. 保持所有现有的markdown格式不变
        3. 每段不超过2-3个加粗
        4. 不要改变任何文字内容
        5. 确保加粗标记成对出现(**)
        
        原文：
        {article}
        
        请直接返回处理后的文章，不要包含任何解释或说明。
        """
        
        return chat(bold_prompt)
    
    def add_highlights(self, article):
        """为文章添加高亮标记"""
        highlight_prompt = f"""
        请为以下文章添加高亮标记(== ==), 要求：
        1. 只给最重要的完整句子添加高亮
        2. 保持所有现有的markdown格式不变（包括加粗标记）
        3. 每段最多高亮一个句子
        4. 高亮的句子应该是该段落的核心观点或结论
        5. 不要改变任何文字内容
        6. 确保高亮标记成对出现(== ==)
        
        原文：
        {article}
        
        请直接返回处理后的文章，不要包含任何解释或说明。
        """
        
        return chat(highlight_prompt)
    
    def process_article(self, article):
        """处理文章：审核、加粗、高亮一条龙服务"""
        reviewed = self.review_article(article)
        with_bold = self.add_bold_marks(reviewed)
        with_highlights = self.add_highlights(with_bold)
        return with_highlights 
    

def process_file(file_path: Union[str, Path]) -> Optional[Path]:
    """处理单个文件的便捷函数"""
    helper = OpenAIHelper()
    file_path = Path(file_path)
    
    try:
        # 读取文章内容
        with open(file_path, 'r', encoding='utf-8') as f:
            article_content = f.read()
        
        print(f"开始处理文章：{file_path.name}")
        
        # 处理文章
        processed_article = helper.process_article(article_content)
        
        # 保存处理后的文章
        output_path = file_path.parent / f"{file_path.stem}-processed{file_path.suffix}"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(processed_article)
        
        print(f"处理完成！文件已保存至：{output_path}")
        return output_path
        
    except FileNotFoundError:
        print(f"错误：找不到文件 {file_path}")
    except Exception as e:
        print(f"处理过程中发生错误：{str(e)}")
    return None

def process_directory(directory: Union[str, Path]) -> List[Path]:
    """处理目录下所有 .md 文件的便捷函数"""
    directory = Path(directory)
    processed_files = []
    
    for md_file in directory.glob("*.md"):
        if result := process_file(md_file):
            processed_files.append(result)
    
    return processed_files

if __name__ == "__main__":
    import argparse
    
    # 设置默认的测试文件
    default_file = "articles/公众号-川普突發行Meme幣TRUMP身價暴漲數倍 一夜暴賺256億美元 梅蘭妮亞搶生意quot第一夫人幣quot上線排擠到川普幣關我什麼事94要賺錢.md"
    
    parser = argparse.ArgumentParser(description='处理 Markdown 文章：添加加粗和高亮')
    parser.add_argument('path', nargs='?', default=default_file, help='要处理的文件或目录路径')
    args = parser.parse_args()
    
    target_path = Path(args.path)
    if target_path.is_file():
        process_file(target_path)
    elif target_path.is_dir():
        processed = process_directory(target_path)
        print(f"\n共处理完成 {len(processed)} 个文件")
    else:
        print(f"错误：路径 {target_path} 无效")