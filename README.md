<<<<<<< HEAD
# YouTube 视频转文章 API 服务

这是一个将 YouTube 视频转换为文章的 API 服务。

## 功能特点

- 支持根据主题搜索 YouTube 视频
- 自动选择最合适的视频
- 将视频转换为文章或文字稿
- 实时显示处理进度
- 支持多种 AI 模型
- Web 界面操作
- 分布式任务队列处理
- 任务进度实时追踪

## 系统要求

- Python 3.9+
- Redis 服务器
- FFmpeg

## 安装

1. 克隆项目：
```bash
git clone <repository_url>
cd youtube_to_article
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
创建 `.env` 文件并添加以下内容：
```
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
YOUTUBE_API_KEY=your_youtube_api_key
REDIS_URL=redis://localhost:6379/0
```

## AI 模型使用说明

本项目使用多个 AI 模型处理不同的任务：

### 1. DeepSeek 模型
- **用途**：分析用户需求，生成搜索关键词
- **API 端点**：`https://api.deepseek.com/v1/chat/completions`
- **模型名称**：`deepseek-chat`
- **主要特点**：
  - 支持中文语义理解
  - 适合生成精准的搜索关键词
  - 响应速度快
  - 支持流式输出

- **请求格式**：
  ```json
  {
    "model": "deepseek-chat",
    "messages": [
      {
        "role": "system",
        "content": "你是一个专业的关键词分析专家，擅长生成高质量的搜索关键词。"
      },
      {
        "role": "user",
        "content": "用户的提示词"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 200,
    "stream": false
  }
  ```

- **请求头**：
  ```json
  {
    "Content-Type": "application/json",
    "Authorization": "Bearer your_deepseek_api_key"
  }
  ```

- **Python 代码示例**：
  ```python
  import requests
  import os
  from typing import List
  
  def generate_keywords(topic: str) -> List[str]:
      headers = {
          "Content-Type": "application/json",
          "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"
      }
      
      data = {
          "model": "deepseek-chat",
          "messages": [
              {
                  "role": "system",
                  "content": "你是一个专业的关键词分析专家，擅长生成高质量的搜索关键词。"
              },
              {
                  "role": "user",
                  "content": f"请根据主题'{topic}'生成5个搜索关键词，每行一个。"
              }
          ],
          "temperature": 0.7,
          "max_tokens": 200,
          "stream": False
      }
      
      response = requests.post(
          "https://api.deepseek.com/v1/chat/completions",
          headers=headers,
          json=data,
          timeout=30
      )
      
      if response.status_code == 200:
          content = response.json()['choices'][0]['message']['content']
          return [keyword.strip() for keyword in content.strip().split("\n")]
      else:
          raise Exception(f"API调用失败: {response.text}")
  ```

- **参数说明**：
  - `model`: 使用的模型名称，固定为 "deepseek-chat"
  - `messages`: 对话历史，包含 system 和 user 角色的消息
  - `temperature`: 控制输出的随机性（0.0-1.0）
  - `max_tokens`: 生成的最大token数
  - `stream`: 是否使用流式输出

- **错误处理**：
  - 网络超时：设置 timeout 参数
  - API 错误：检查 response.status_code
  - 格式错误：使用 try-except 捕获 JSON 解析错误
  - 内容验证：检查生成的关键词数量和质量

- **最佳实践**：
  1. 始终设置合理的超时时间
  2. 实现错误重试机制
  3. 验证 API 密钥的有效性
  4. 记录详细的错误日志
  5. 对生成的关键词进行质量检查

- **使用限制**：
  - 需要有效的 DeepSeek API 密钥
  - 请求频率限制
  - 单次生成的 token 数限制
  - API 调用额度限制

- **注意事项**：
  1. 保护好 API 密钥
  2. 监控 API 使用量
  3. 处理好超时和错误情况
  4. 确保生成的关键词符合要求
  5. 定期检查 API 的可用性

### 2. OpenAI Whisper
- **用途**：音频转文字
- **模型名称**：`whisper-1`
- **使用场景**：将视频音频转换为文本

### 3. GPT-3.5-Turbo
- **用途**：优化文章内容
- **模型名称**：`gpt-3.5-turbo`
- **使用场景**：文章生成、内容优化

### 4. fine-tune GPT模型
- **用途**：生成文章
- **模型名称**：`ft:gpt-4o-mini-2024-07-18:1234::Aj1D4Hzr`
- **使用场景**：公众号文章生成

## 运行服务

1. 启动 Redis 服务器：
```bash
redis-server
```

2. 启动 Celery Worker：
```bash
python src/run_worker.py
```

3. 启动 Flower（可选，用于监控任务）：
```bash
celery -A src.celery_app.celery_app flower
```

4. 启动 API 服务：
```bash
python src/run_api.py
```

5. 访问服务：
- Web 界面：http://localhost:8000
- Flower 监控：http://localhost:5555

## API 接口

### 1. 创建处理任务
- URL: `/api/process`
- 方法: POST
- 参数:
  ```json
  {
    "topic": "视频主题",
    "mode": "1"  // 1: 公众号文章, 2: 文字稿
  }
  ```
- 返回:
  ```json
  {
    "task_id": "任务ID",
    "status": "pending",
    "message": "任务已创建，正在处理中..."
  }
  ```

### 2. 获取任务状态
- URL: `/api/status/{task_id}`
- 方法: GET
- 返回:
  ```json
  {
    "status": "processing",
    "progress": 0.5,
    "message": "正在处理...",
    "result": null
  }
  ```

### 3. 健康检查
- URL: `/api/health`
- 方法: GET
- 返回:
  ```json
  {
    "status": "healthy",
    "message": "Service is running",
    "timestamp": 1703913600
  }
  ```

## 使用的 AI 模型

- OpenAI Whisper: 音频转文字
- GPT-4o-mini: 生成文章
- GPT-3.5-Turbo: 审核和修改文章
- DeepSeek: 评估视频相关性

## 任务队列说明

系统使用 Celery 和 Redis 实现分布式任务队列：

1. **任务状态**：
   - pending: 等待处理
   - processing: 处理中
   - completed: 处理完成
   - failed: 处理失败

2. **任务监控**：
   - 使用 Flower 监控任务执行情况
   - 实时查看任务进度
   - 查看任务历史记录
   - 监控 worker 状态

3. **错误处理**：
   - 自动重试失败任务
   - 记录详细错误信息
   - 任务超时保护

4. **扩展性**：
   - 支持多个 worker
   - 可横向扩展
   - 任务优先级支持

## 注意事项

1. 确保有稳定的网络连接
2. API 密钥需要有足够的额度
3. 视频和音频文件有大小限制
4. 处理时间取决于视频长度和网络状况
5. Redis 服务需要正常运行
6. Worker 需要保持在线

## 许可证

MIT License

## 工作流程

系统的工作流程分为以下几个步骤：

### 1. 分析用户需求（10%）
- **使用模型**：DeepSeek Chat
- **模型名称**：`deepseek-chat`
- **功能**：分析用户输入的主题，生成5个相关的搜索关键词
- **输出**：搜索关键词列表

### 2. 搜索相关视频（20%）
- **使用工具**：YouTube Search API
- **功能**：根据生成的关键词搜索相关视频
- **输出**：每个关键词返回3个相关视频，共15个视频

### 3. 选择最佳视频（30%）
- **使用模型**：DeepSeek Chat
- **模型名称**：`deepseek-chat`
- **功能**：评估每个视频的相关性和质量
- **输出**：选择得分最高的视频

### 4. 下载视频（40%）
- **使用工具**：yt-dlp
- **功能**：下载选中视频并提取音频
- **输出**：MP3格式的音频文件

### 5. 转录音频（60%）
- **使用模型**：OpenAI Whisper
- **模型名称**：`whisper-1`
- **功能**：将音频转换为文本
- **预处理**：
  - 检查音频文件大小
  - 如果超过25MB，使用ffmpeg压缩
- **输出**：音频的文字转录

### 6. 生成文章（80%）
1. **预处理转录文本**
   - **使用模型**：DeepSeek Chat
   - **模型名称**：`deepseek-chat`
   - **功能**：提取转录文本中的关键信息
   - **输出**：精简后的关键信息（<500字）

2. **生成文章大纲**
   - **使用模型**：DeepSeek Chat
   - **模型名称**：`deepseek-chat`
   - **功能**：根据视频信息和关键信息生成文章大纲
   - **输出**：结构化的文章大纲

3. **生成文章内容**
   - **使用模型**：Fine-tuned GPT-4
   - **模型名称**：`ft:gpt-4o-mini-2024-07-18:1234::Aj1D4Hzr`
   - **功能**：根据大纲和关键信息生成完整文章
   - **输出**：markdown格式的文章

### 7. 验证文章（90%）
- **使用模型**：DeepSeek Chat
- **模型名称**：`deepseek-chat`
- **功能**：
  - 检查文章字数（1000-1500字）
  - 验证段落数量（≥10段）
  - 检查文章格式
  - 必要时修复和优化内容
- **输出**：验证结果和修复后的文章

### 8. 保存和清理（100%）
- **功能**：
  - 将文章保存到 `data/articles` 目录
  - 清理临时文件（下载的视频、音频等）
- **输出**：保存的文章路径

## 系统架构

### 1. 核心组件
- **WorkflowProcessor**: 工作流程控制器
- **OpenAIHelper**: OpenAI API 接口封装
- **DeepseekHelper**: DeepSeek API 接口封装
- **YouTubeSearch**: YouTube 搜索功能封装

### 2. 依赖服务
- **Redis**: 任务队列和缓存
- **Celery**: 分布式任务处理
- **FFmpeg**: 音视频处理
- **yt-dlp**: YouTube 视频下载

### 3. API服务
- **FastAPI**: Web API 框架
- **Flower**: Celery 任务监控

## 配置说明

### 1. 环境变量
```bash
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
YOUTUBE_API_KEY=your_youtube_api_key
REDIS_URL=redis://localhost:6379/0
```

### 2. 模型配置
- **OpenAI Whisper**
  - 模型：whisper-1
  - 最大音频大小：25MB
  - 支持格式：mp3, mp4, mpeg, mpga, m4a, wav, webm

- **DeepSeek Chat**
  - 模型：deepseek-chat
  - 最大输入长度：4096 tokens
  - 最大输出长度：2048 tokens
  - 支持流式输出

- **Fine-tuned GPT-4**
  - 模型：ft:gpt-4o-mini-2024-07-18:1234::Aj1D4Hzr
  - 特点：针对文章生成任务优化
  - 支持中文创作

### 3. 文件目录结构
```
youtube_to_article/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── workflow_processor.py
│   ├── celery_app.py
│   ├── api.py
│   └── utils/
│       ├── __init__.py
│       ├── deepseek_helper.py
│       └── openai_helper.py
├── data/
│   └── articles/
├── tests/
├── requirements.txt
├── README.md
└── .env
```

## 性能优化

### 1. 音频处理
- 自动压缩大于25MB的音频文件
- 使用ffmpeg优化音频质量
- 并行处理多个音频文件

### 2. 任务处理
- 使用Celery实现异步任务处理
- Redis作为消息代理
- 支持任务重试和错误处理

### 3. API性能
- 支持异步请求处理
- 实现请求限流
- 缓存常用数据

## 错误处理

### 1. 视频下载
- 自动重试失败的下载
- 支持断点续传
- 检查视频可用性

### 2. 音频转录
- 音频格式验证
- 大小限制检查
- 转录质量验证

### 3. 文章生成
- 内容质量检查
- 字数和格式验证
- 自动修复问题

## 监控和日志

### 1. 任务监控
- Flower监控面板
- 任务状态追踪
- 性能指标统计

### 2. 日志记录
- 详细的处理日志
- 错误追踪
- 性能分析

### 3. 告警机制
- 任务失败告警
- 系统异常通知
- 资源使用预警

## 安全措施

### 1. API安全
- API密钥管理
- 请求认证
- 访问控制

### 2. 数据安全
- 敏感信息加密
- 临时文件安全清理
- 数据备份机制

### 3. 系统安全
- 依赖包安全检查
- 定期安全更新
- 访问日志审计

## 部署说明

### 1. 本地开发环境
```bash
# 1. 克隆项目
git clone <repository_url>
cd youtube_to_article

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的API密钥

# 5. 启动Redis
redis-server

# 6. 启动Celery Worker
celery -A src.celery_app.celery_app worker --loglevel=info

# 7. 启动Flower（可选）
celery -A src.celery_app.celery_app flower

# 8. 启动API服务
uvicorn src.api:app --reload
```

### 2. 生产环境部署
```bash
# 1. 安装依赖
apt-get update
apt-get install -y ffmpeg redis-server python3-pip

# 2. 配置系统服务
# 创建systemd服务文件
# 配置supervisor
# 设置nginx反向代理

# 3. 启动服务
systemctl start redis
systemctl start celery
systemctl start api
```

## 常见问题

### 1. 视频下载问题
- 检查YouTube API配额
- 验证网络连接
- 确认视频可访问性

### 2. 音频转录问题
- 检查音频文件格式
- 验证文件大小
- 确认API密钥有效性

### 3. 文章生成问题
- 检查模型可用性
- 验证输入数据
- 确认字数限制

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持基本的视频转文章功能
- 实现异步任务处理

### v1.1.0 (2024-01-15)
- 添加音频压缩功能
- 优化文章生成质量
- 改进错误处理机制

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

- 项目维护者：[维护者姓名]
- 邮箱：[联系邮箱]
- GitHub：[GitHub地址]
=======
# titicacine
>>>>>>> 2d8109e5f40080bace2ee2c2b9f7d31abbce54c2
