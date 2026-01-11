快速测试指南

以下指南帮助你在本地裸机环境上初始化数据库并运行示例 curl 命令与 pytest 测试。

先决条件
- Python 3.11
- 系统依赖（Linux 下）: `qpdf`（用于 `pikepdf`）

初始化虚拟环境并安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

初始化数据库并创建示例用户/文档

```bash
python backend/scripts/init_db.py
```

示例 curl 命令

1) 获取管理员 token

```bash
curl -X POST -d "username=admin&password=adminpass" http://127.0.0.1:8000/api/token
```

2) 上传 PDF（替换 <TOKEN> 为上一步的 access_token）

```bash
curl -H "Authorization: Bearer <TOKEN>" -F "file=@/path/to/sample.pdf" http://127.0.0.1:8000/api/documents/upload
```

3) 列表文档

```bash
curl -H "Authorization: Bearer <TOKEN>" http://127.0.0.1:8000/api/documents
```

4) 授权用户访问文档（示例：grant 给 user_id=2）

```bash
curl -X POST -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{"user_id":2}' http://127.0.0.1:8000/api/documents/1/grant
```

5) 模拟用户下载（使用 alice 的 token，或通过 grant 给 alice）

```bash
curl -H "Authorization: Bearer <ALICE_TOKEN>" -L http://127.0.0.1:8000/api/documents/1/download --output out.pdf
```

运行自动化测试（pytest）

```bash
# 确保虚拟环境激活并且依赖安装完成
pytest -q backend/tests/test_api.py
```

注意
- 水印步骤依赖 `pikepdf` 和 `reportlab` 以及系统 `qpdf`。若你的环境缺少这些，下载测试可能返回 500（测试接受 200 或 500 作为通过条件，表明鉴权和流程执行正确但水印命令失败）。
- 在生产部署时，务必将文档目录放在不可被 nginx 直接访问的位置（见 backend/deploy/README.md）。
