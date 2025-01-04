from typing import Optional
from src.workflow_processor import WorkflowProcessor
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import sys

# 配置日志
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 文件处理器
file_handler = logging.FileHandler('app.log', mode='w')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# 控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

app = Flask(__name__)
CORS(app)  # 启用 CORS 支持

def generate_article(topic: str) -> str:
    """生成文章的主函数"""
    try:
        logger.info(f"开始生成文章，主题: {topic}")
        
        # 创建工作流处理器
        processor = WorkflowProcessor()
        
        # 使用异步方式处理主题
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        result = loop.run_until_complete(processor.process_topic(topic))
        
        # 如果处理成功
        if result and result.get('status') == 'success':
            # 返回处理结果
            video = result['video']
            article = result['article']
            keywords = result.get('keywords', [])
            main_points = result.get('main_points', [])
            insights = result.get('insights', [])
            
            logger.info(f"文章生成成功，视频标题: {video['title']}")
            
            # 格式化主要观点
            points_text = "\n".join([f"- {point}" for point in main_points])
            
            # 格式化见解
            insights_text = "\n".join([f"- {insight}" for insight in insights])
            
            return f"""# {topic}

## 视频来源
- 标题：{video['title']}
- 链接：{video['url']}
- 描述：{video['description']}

## 关键词
{', '.join(keywords)}

## 主要观点
{points_text}

## 重要见解
{insights_text}

## 文章内容
{article}
"""
        else:
            error_msg = result.get('error', '未知错误')
            logger.error(f"处理失败: {error_msg}")
            return f"处理失败: {error_msg}"
        
    except Exception as e:
        logger.error(f"生成文章时出错: {str(e)}")
        return f"生成文章时出错: {str(e)}"
    finally:
        try:
            loop.close()
        except:
            pass

@app.route('/api/generate_article', methods=['POST'])
def api_generate_article():
    try:
        logger.info("收到生成文章请求")
        data = request.get_json()
        if not data:
            logger.error("无效的请求数据")
            return jsonify({"error": "无效的请求数据"}), 400
            
        if 'title' not in data:
            logger.error("缺少标题参数")
            return jsonify({"error": "缺少标题参数"}), 400
            
        title = data['title']
        logger.info(f"开始处理标题: {title}")
        
        article = generate_article(title)
        logger.info("文章生成完成")
        return jsonify({"article": article})
        
    except Exception as e:
        logger.error(f"API错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 使用环境变量或默认值设置端口
    port = int(os.getenv('FLASK_PORT', 5002))
    logger.info(f"启动Flask服务器，端口: {port}")
    app.run(host='0.0.0.0', port=port, debug=True)