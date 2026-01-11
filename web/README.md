开发说明

1. 安装依赖

```bash
cd web
npm install
```

2. 运行开发服务器

```bash
npm start
```

3. 配置 API 地址

复制 `.env.example` 为 `.env` 并修改 `REACT_APP_API_BASE` 为后端地址，例如 `http://localhost:8000/api`。

备注
- 前端示例仅实现简单的文档列表与上传界面，管理员接口需要使用带有 JWT 的请求头 `Authorization: Bearer <token>`。
- 生产环境建议使用 `npm run build` 并将 `build/` 目录放到 Nginx 静态根。