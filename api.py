from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

# 首页
@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>服务启动成功！✅</h1>"

# 测试接口
@app.get("/test")
def test():
    return {"msg": "FastAPI 运行正常"}

# 本地启动
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
