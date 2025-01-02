#!/bin/bash

# 使用scp上传更新后的requirements.txt文件
scp -P 17471 \
    requirements.txt \
    root@45.192.101.86:/var/www/myproject/

# 连接到服务器并重新安装依赖
ssh -p 17471 root@45.192.101.86 << 'EOF'
cd /var/www/myproject
deactivate || true  # 如果有激活的虚拟环境就退出
rm -rf venv  # 删除现有虚拟环境
python3.9 -m venv venv  # 创建新的虚拟环境
source venv/bin/activate  # 激活虚拟环境
pip install --upgrade pip  # 更新pip
pip install -r requirements.txt  # 安装新的依赖
EOF 