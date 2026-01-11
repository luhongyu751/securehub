部署说明（裸机，示例基于 Ubuntu 22.04）

概述
- 本项目后端基于 FastAPI，前端为 React + Material UI（位于 `web/`）。
- 文档文件应放在受保护的位置（非 nginx 静态根），所有下载必须经过后端鉴权并调用 `backend/modules/add.py` 加水印后再返回，防止绕过。

先决条件
- 目标为 Ubuntu/Debian 系统（若为 CentOS/RHEL，命令请做等效替换）。
- 安装 Python 3.11、pip、virtualenv，以及 Nginx。

关键路径（快速步骤）
1. 创建运行用户与目录

```bash
# 以 root 或 sudo 执行
useradd --system --create-home --home /opt/securehub securehub
mkdir -p /opt/securehub
chown securehub:securehub /opt/securehub
```

2. 将仓库代码拷贝到服务器 `/opt/securehub`（或使用 git clone）

3. 创建虚拟环境并安装依赖

```bash
apt update
apt install -y python3.11 python3.11-venv python3-pip nginx
sudo -u securehub python3.11 -m venv /opt/securehub/venv
/opt/securehub/venv/bin/pip install --upgrade pip
/opt/securehub/venv/bin/pip install -r /opt/securehub/requirements.txt
```

注意：`pikepdf` 需要系统依赖 `qpdf`：

```bash
apt install -y qpdf
```

4. 创建文档存储目录（不可被 nginx 直接访问）

```bash
mkdir -p /var/securehub/documents
chown securehub:securehub /var/securehub/documents
chmod 770 /var/securehub/documents
```

5. 配置 systemd 服务
- 文件：`/etc/systemd/system/securehub.service`，示例请参考 `backend/deploy/securehub.service`。

```bash
systemctl daemon-reload
systemctl enable securehub
systemctl start securehub
journalctl -u securehub -f
```

6. 配置 Nginx
- 示例配置文件在 `backend/nginx.conf.sample`。
- 关键点：
  - 将 `/api/` 反向代理到 `http://127.0.0.1:8000/`。
  - 不要把 `/var/securehub/documents` 或后端私有目录映射为静态根。所有下载请求要走后端接口。 

7. TLS（可选但强烈建议）
- 使用 Certbot 获取证书并自动配置 Nginx：

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d example.com
```

8. 权限与安全注意事项
- 将文档目录权限限制为运行用户 `securehub`，并确保 nginx 不能直接访问。
- 后端下载接口必须校验 JWT/2FA/权限：不要在任何地方直接暴露文件系统路径给用户。
- 使用 `backend/deploy/watermark_wrapper.py`（或在后端内调用类似逻辑）以受控方式执行 `add.py`，并使用临时文件返回给客户端后删除。
- 日志记录下载事件并保留链路（用户名、时间、document id、客户端 IP）。

9. 启动验证
- 访问后端健康检查：

```bash
curl -v http://127.0.0.1:8000/health
```

- 通过 Nginx 访问站点根，检查是否能正确代理到前端/后端。

附录
- systemd 单元示例：`backend/deploy/securehub.service`
- 安全水印封装脚本：`backend/deploy/watermark_wrapper.py`

如果需要，我可以：
- 在后端实现受控下载接口示例（含调用 `watermark_wrapper.py`、鉴权与日志记录）。
- 生成用于 `nginx` 的完整生产配置（包含 Let's Encrypt 示例）。
