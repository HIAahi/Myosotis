from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

# 首页接口
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <h1>✅ FastAPI 服务启动成功！</h1>
    <p>访问 <a href="/docs">/docs</a> 查看接口文档</p>
    """

# 测试接口
@app.get("/test")
async def test():
    return {"status": "ok", "message": "服务运行正常"}

# 本地启动入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
