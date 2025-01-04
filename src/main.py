from typing import Optional
from src.workflow_processor import WorkflowProcessor
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@app.route('/api/generate_article', methods=['POST'])
def generate_article_endpoint():
    """处理生成文章的请求"""
    try:
        logger.info("收到生成文章请求")
        data = request.get_json()
        if not data or 'title' not in data:
            logger.error("无效的请求数据")
            return jsonify({"error": "无效的请求数据"}), 400
            
        title = data['title']
        logger.info(f"开始处理标题: {title}")
        
        # 创建工作流处理器
        processor = WorkflowProcessor()
        
        # 使用异步方式处理主题
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        result = loop.run_until_complete(processor.process_topic(title))
        
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
            
            response = {
                "video": {
                    "title": video['title'],
                    "url": video['url'],
                    "description": video['description']
                },
                "keywords": keywords,
                "main_points": main_points,
                "insights": insights,
                "article": article
            }
            
            return jsonify(response)
        else:
            error_msg = result.get('error', '未知错误')
            logger.error(f"处理失败: {error_msg}")
            return jsonify({"error": error_msg}), 500
            
    except Exception as e:
        logger.error(f"API错误: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            loop.close()
        except:
            pass

if __name__ == '__main__':
    # 使用环境变量或默认值设置端口
    port = int(os.getenv('FLASK_PORT', 5001))
    logger.info(f"启动Flask服务器，端口: {port}")
    app.run(host='0.0.0.0', port=port, debug=True)