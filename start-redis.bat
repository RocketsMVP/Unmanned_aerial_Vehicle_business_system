@echo off
echo ========================================
echo    启动 Redis 服务 (本机原生方式)
echo ========================================
echo.
echo [信息] 使用完整路径启动 Redis (D:\Redis)...
echo 端口: 6379
echo 密码: 请在 redis.conf 中查看或自行配置
echo 配置: redis.conf
echo.

:: 创建数据目录
if not exist "data\redis" (
    mkdir "data\redis"
    echo [信息] 已创建数据目录: data\redis
)

echo.
echo [启动中...] 请勿关闭此窗口
echo.

:: 使用完整路径启动 Redis（不依赖环境变量）
D:\Redis\redis-server.exe "%~dp0redis.conf"

pause
