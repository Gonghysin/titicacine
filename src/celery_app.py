from celery import Celery
from src.workflow_processor import WorkflowProcessor
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取Redis URL
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

# 创建Celery实例
celery_app = Celery(
    'youtube_to_article',
    broker=redis_url,
    backend=redis_url,
    broker_connection_retry_on_startup=True
)

# 配置Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    worker_max_tasks_per_child=50,  # 处理50个任务后重启worker
    worker_prefetch_multiplier=1  # 每个worker一次只处理一个任务
)

@celery_app.task(bind=True)
def process_video_task(self, topic: str, mode: str):
    """处理视频的 Celery 任务"""
    try:
        def progress_callback(progress: float, message: str):
            """更新任务进度"""
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': progress,
                    'message': message,
                    'result': None
                }
            )
        
        # 初始化处理器
        processor = WorkflowProcessor(progress_callback=progress_callback)
        
        # 处理视频
        result = processor.process_workflow(topic, mode)
        
        if result:
            return {
                'status': 'completed',
                'progress': 1.0,
                'message': '处理完成',
                'result': result
            }
        else:
            return {
                'status': 'failed',
                'progress': 1.0,
                'message': '处理失败',
                'result': None
            }
            
    except Exception as e:
        return {
            'status': 'failed',
            'progress': 1.0,
            'message': f'处理出错: {str(e)}',
            'result': None
        } 