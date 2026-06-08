# go-cqhttp + qsign 签名服务器部署

QQ 机器人部署在 Hermes 服务器上的完整流程。

## 组件

| 组件 | 端口 | 说明 |
|------|------|------|
| **go-cqhttp** | 5700 (HTTP API) | QQ 协议实现，暴露 HTTP API 供 Hermes 调用 |
| **qsign** | 8800 | 签名服务器，解决 QQ 登录风控和协议签名问题 |

## 安装步骤

### 1. go-cqhttp

```bash
# 下载 linux amd64 版本
cd /tmp
curl -L -o gocqhttp.tar.gz \
  "https://github.com/Mrs4s/go-cqhttp/releases/download/v1.2.0/go-cqhttp_linux_amd64.tar.gz"

# 解压
mkdir -p /home/ubuntu/gocqhttp
cd /home/ubuntu/gocqhttp
tar xzf /tmp/gocqhttp.tar.gz

# 首次运行生成 config.yml（选择 HTTP 通信方式）
cd /home/ubuntu/gocqhttp
echo -e "3\n" | ./go-cqhttp  # 输入 0 启用 HTTP 通信

# 修改 config.yml 配置账号和签名服务器
```

### 2. qsign 签名服务器（Docker）

```bash
docker run -d \
  --name qsign \
  --restart unless-stopped \
  -p 8800:80 \
  bennettwu/qsign-server:latest
```

验证：
```bash
curl -s http://localhost:8800/
# 返回: {"code":0,"msg":"IAA ...","data":{"version":"1.1.9",...}}
```

## go-cqhttp 配置要点

### config.yml 关键字段

```yaml
account:
  uin: 123456789        # QQ 号，必填
  password: ''           # 空=扫码登录，填密码=密码登录
  sign-servers:
    - url: 'http://172.17.0.1:8800'  # Docker 容器通过宿主机网桥访问 qsign
      key: '114514'

servers:
  - http:
      host: 0.0.0.0
      port: 5700           # HTTP API 端口
```

**注意：** `sign-servers.url` 使用 `172.17.0.1`（Docker 网桥网关）而非 `localhost`，因为 go-cqhttp 运行在宿主机上而 qsign 在 Docker 容器中。反过来如果 go-cqhttp 也在 Docker 中，则用容器名互相访问。

### Caddy 反代（可选）

如果想把 go-cqhttp 的 HTTP API 暴露到公网（不推荐，建议仅在局域网/内网使用）：

```caddyfile
qqbot.zaiyemeiyou.com {
    tls internal
    reverse_proxy 172.17.0.1:5700
}
```

## 登录方式

### 扫码登录（推荐首次）
- config.yml 中 `password: ''`
- 运行 `./go-cqhttp`，终端输出二维码图片路径
- 用手机 QQ 扫码

### 密码登录
```yaml
account:
  uin: 123456789
  password: 'your_password'
```

## 常见问题

### 重启流程（拿到新的验证 URL）

重启 go-cqhttp 时，先 `process(action="write", data="\\x03")` 发送 Ctrl+C，然后 `process(action="kill", session_id="<id>")` 确保进程已清理。**必须删除旧日志**（`rm -f /home/ubuntu/gocqhttp/logs/*.log`），否则新进程会写入同一日志文件造成混乱。

### 首次登录触发滑块验证码

go-cqhttp 首次登录时会提示需要滑块验证码，交互流程如下：

1. go-cqhttp 打印提示："登录需要滑条验证码, 请验证后重试。请选择提交滑块ticket方式：1. 自动提交 2. 手动抓取提交"
2. 如果进程在后台运行（`process(action="submit", data="2")`），需要发送 `2` 选择手动模式
3. 等待后 go-cqhttp 会打印一个验证 URL：
   ```
   请前往该地址验证 -> https://ti.qq.com/safe/tools/captcha/sms-verify-login?...
   ```
4. 将 URL 发给用户在手机/电脑浏览器打开，完成滑块验证后获得 ticket 字符串
5. 将 ticket 提交回进程：`process(action="submit", data="<ticket>")`

**注意：** 验证 URL 有时效性，过期后需要重启 go-cqhttp 获取新 URL：

```bash
# 1. 向进程发送 Ctrl+C
process(action="kill", session_id="<id>")

# 2. 删除旧日志
rm -f /home/ubuntu/gocqhttp/logs/*.log

# 3. 重新启动
terminal(command="cd /home/ubuntu/gocqhttp && ./go-cqhttp", background=true, watch_patterns=["前往该地址"])
```

### T544 sign 错误
日志中出现 `获取T544 sign时出现错误: encoding/hex: invalid byte: U+002F '/'`，这是 qsign 收到含 `/` 的请求时 hex 编码失败。虽然打印为 WARNING，但**不影响登录流程**，go-cqhttp 仍可继续进入滑块验证步骤。

### 登录 45 错误 / 需要滑块验证
- qsign 版本过低或协议版本不匹配
- 检查 qsign 返回的 protocol.version，确保与 go-cqhttp 兼容
- 可尝试使用 `xzhouqd/qsign` 镜像（tag 指定版本）

### 签名服务器连接不上
- 检查 Docker 是否在运行：`docker ps | grep qsign`
- 检查端口：`curl -s http://localhost:8800/`
- 容器内 go-cqhttp 用 `172.17.0.1:8800`，宿主机 go-cqhttp 用 `localhost:8800` 或 `127.0.0.1:8800`

### 消息风控 / 发送失败
- 签名服务器版本过低
- qsign 的协议版本需与腾讯当前强制版本匹配
- 参考：https://github.com/fuqiuluo/unidbg-fetch-qsign

## API 使用

go-cqhttp 启动后 HTTP API 地址：`http://localhost:5700`

常用接口：
- `GET /send_private_msg?user_id=QQ号&message=hello` — 发送私聊
- `GET /send_group_msg?group_id=群号&message=hello` — 发送群消息
- `GET /get_login_info` — 获取当前登录账号信息

参考文档：https://docs.go-cqhttp.org/api
