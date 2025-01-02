操作系统：Ubuntu-20.04.1-x64
IP:45.192.101.86
端口：17471
用户名:root
密码:C0df4a6ebe

# SSH 登录到服务器
ssh -p 17471 root@45.192.101.86

# 进入项目目录并执行部署脚本
cd /var/www/myproject
chmod +x deploy.sh
./deploy.sh
