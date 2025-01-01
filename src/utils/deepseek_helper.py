import os
from openai import OpenAI
from typing import List

class DeepseekHelper:
    def __init__(self):
        """初始化 DeepSeek 助手"""
        self.client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com/v1"
        )
    
    def analyze_topic(self, topic: str) -> List[str]:
        """分析主题并生成搜索关键词"""
        try:
            model_name = "deepseek-chat"
            print(f"\n=== 使用 {model_name} 模型分析主题和生成关键词 ===")
            prompt = f"""
            请根据以下主题生成5个中文搜索关键词，用于在YouTube上搜索相关视频：
            
            主题：{topic}
            
            要求：
            1. 每个关键词2-4个词
            2. 关键词要具体且相关
            3. 关键词要包含主题的核心内容
            4. 关键词要有助于找到高质量的视频
            5. 直接返回关键词列表，每行一个
            
            请生成关键词：
            """
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的关键词分析专家，擅长生成高质量的搜索关键词。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            keywords = [
                keyword.strip()
                for keyword in content.strip().split("\n")
                if keyword.strip()
            ]
            
            return keywords
            
        except Exception as e:
            print(f"分析主题时出错: {str(e)}")
            return []
    
    def score_content(self, topic: str, content: str) -> float:
        """评分内容相关性"""
        try:
            model_name = "deepseek-chat"
            print(f"\n=== 使用 {model_name} 模型评分视频相关性 ===")
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的内容评分专家。你的任务是评估内容与主题的相关性，并返回一个0到5之间的数字分数。只返回数字，不要包含任何其他文字。"},
                    {"role": "user", "content": f"请评估以下内容与主题「{topic}」的相关性（0-5分）：\n\n{content}"}
                ],
                temperature=0.3,
                max_tokens=10
            )
            
            text = response.choices[0].message.content.strip()
            return float(''.join(c for c in text if c.isdigit() or c == '.'))
            
        except Exception as e:
            print(f"DeepSeek评分出错: {str(e)}")
            return 0.0
    
    def review_article(self, article: str, prompt: str = None) -> str:
        """审核和修改文章"""
        try:
            model_name = "deepseek-chat"
            print(f"\n=== 使用 {model_name} 模型审核和修改文章 ===")
            
            if not prompt:
                prompt = f"""
                请仔细审核并修改以下文章。你的任务是：
                1. 确保文章字数在1000-1500字之间：
                   - 如果字数不足，通过以下方式补充：
                     * 扩展现有论点
                     * 添加相关例子
                     * 补充必要的背景信息
                   - 如果字数过多，通过以下方式精简：
                     * 删除次要信息
                     * 合并相似内容
                     * 简化表述方式
                
                2. 保持文章结构完整：
                   - 确保有清晰的开头、主体和结尾
                   - 至少包含10个段落
                   - 每个段落60-80字
                   - 段落之间要有逻辑连接
                
                3. 维持markdown格式：
                   - 保留所有markdown标记
                   - 确保标题层级正确
                   - 保持段落间的空行
                   - 保留加粗等格式
                
                4. 优化内容质量：
                   - 确保内容准确、专业
                   - 修正不通顺的句子
                   - 改善表达方式
                   - 增强文章可读性
                
                5. 注意事项：
                   - 不要返回任何解释或说明
                   - 直接返回修改后的文章
                   - 不要改变文章的主要观点
                   - 保持文章的原有风格
                
                需要修改的文章：
                {article}
                
                请直接返回修改后的文章，不要包含任何其他内容："""
            
            # 最多尝试3次生成
            for attempt in range(3):
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": """你是一个专业的文章审核专家，擅长优化和修改文章。你的工作原则是：
1. 严格遵守字数限制（1000-1500字）
2. 保持文章结构完整
3. 维护markdown格式
4. 确保内容质量
5. 直接返回修改后的文章，不包含任何解释或说明"""},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )
                
                result = response.choices[0].message.content.strip()
                
                # 验证生成的内容
                if len(result) < 100 or "不能生成" in result or "抱歉" in result:
                    print(f"第{attempt + 1}次生成的内容无效，重试...")
                    continue
                    
                # 检查是否包含markdown格式
                if not any(line.startswith('#') for line in result.split('\n')):
                    print(f"第{attempt + 1}次生成的内容缺少markdown格式，重试...")
                    continue
                    
                # 计算中文字数
                chinese_chars = len([c for c in result if '\u4e00' <= c <= '\u9fff'])
                if chinese_chars < 1000 or chinese_chars > 1500:
                    print(f"第{attempt + 1}次生成的内容字数不符合要求（{chinese_chars}字），重试...")
                    continue
                
                return result
            
            # 如果所有尝试都失败，返回原文
            print("所有修改尝试都失败，返回原文")
            return article
            
        except Exception as e:
            print(f"审核文章时出错: {str(e)}")
            return article
