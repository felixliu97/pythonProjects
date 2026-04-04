#!/bin/bash

# 1. 确保后端正在运行，或者从静态文件导出
# 建议：在 CI 环境中，可以使用 python -c "import json; from main import app; print(json.dumps(app.openapi()))" > openapi.json

# 2. 使用 Hey API 生成客户端
# 这里的 URL 应该是你 FastAPI 运行的地址
echo "Generating TypeScript client from FastAPI OpenAPI spec..."

# 获取脚本所在目录的上一级目录 (项目根目录)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 在 frontend 目录下运行 openapi-ts，它会自动读取 openapi-ts.config.ts
cd "$PROJECT_ROOT/frontend" && npx @hey-api/openapi-ts

echo "Done! You can now import services from ./src/api-client"
