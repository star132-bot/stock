# Stock Dashboard 公网访问方案

## 当前方案

当前项目还是纯前端静态原型，最轻量的公网访问方式是：

1. 本地启动静态服务
2. 用 `cloudflared` 把本地端口映射到公网
3. 把生成的 `trycloudflare.com` 地址发给别人访问

这套方案适合：

- 临时演示
- 远程查看
- 先验证页面交互

这套方案不适合：

- 长期稳定生产访问
- 需要固定域名和权限控制的正式环境

## 已加入的脚本

- 启动本地服务：
  [start_local_server.sh](/Users/starfeld/project/stock-realtime-dashboard/scripts/start_local_server.sh)
- 启动公网分享：
  [start_public_share.sh](/Users/starfeld/project/stock-realtime-dashboard/scripts/start_public_share.sh)
- 查询当前公网地址：
  [query_public_share.sh](/Users/starfeld/project/stock-realtime-dashboard/scripts/query_public_share.sh)
- 停止服务和隧道：
  [stop_public_share.sh](/Users/starfeld/project/stock-realtime-dashboard/scripts/stop_public_share.sh)

## 使用方法

在项目目录执行：

```bash
cd /Users/starfeld/project/stock-realtime-dashboard
bash scripts/start_public_share.sh
```

默认会：

- 启动本地静态服务：`http://127.0.0.1:8130`
- 启动 Cloudflare Tunnel
- 输出一个类似下面的公网地址：

```text
https://xxxx-xxxx-xxxx.trycloudflare.com
```

如果你只想本地预览：

```bash
bash scripts/start_local_server.sh
```

停止时执行：

```bash
bash scripts/stop_public_share.sh
```

如果你只想查询当前公网地址和运行状态：

```bash
bash scripts/query_public_share.sh
```

## 运行状态文件

脚本会把运行信息写到：

- 本地服务日志：`.runtime/local-server.log`
- Tunnel 日志：`.runtime/cloudflared.log`
- 本地地址：`.runtime/local-server.url`
- 公网地址：`.runtime/public-share.url`
- 本地服务 PID：`.runtime/local-server.pid`
- Tunnel PID：`.runtime/cloudflared.pid`

## 后续迁移到服务器的路径

等你买服务器后，建议直接走正式部署，不再依赖临时 `trycloudflare` 域名。

推荐路线：

1. 把当前静态前端部署到服务器 Nginx
2. 后端市场数据网关部署成独立服务
3. 用 Cloudflare 做正式域名接入和 HTTPS
4. 前端域名例如：
   `stock.yourdomain.com`
5. API 域名例如：
   `api-stock.yourdomain.com`

## 推荐生产结构

- 前端：静态资源，Nginx 托管
- 后端：REST + WebSocket 网关
- 反向代理：Nginx / Caddy
- 域名接入：Cloudflare DNS + SSL
- 进程托管：systemd / pm2 / docker compose

## 为什么现在先用 Cloudflare Tunnel

- 不需要先买服务器
- 不需要公网 IP
- 不需要改路由器
- 适合先把原型发给别人看

## 注意事项

- `trycloudflare.com` 是临时地址，重启后通常会变
- 本机关闭、休眠、断网后公网地址会失效
- 当前项目没有登录和访问控制，不适合直接放正式敏感数据
