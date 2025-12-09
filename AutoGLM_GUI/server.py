"""AutoGLM-GUI Backend API Server."""

from importlib.metadata import version as get_version
from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from AutoGLM_GUI.phone_agent import PhoneAgent
from AutoGLM_GUI.phone_agent.adb import get_screenshot
from AutoGLM_GUI.phone_agent.agent import AgentConfig
from AutoGLM_GUI.phone_agent.model import ModelConfig

# 获取包版本号
try:
    __version__ = get_version("autoglm-gui")
except Exception:
    __version__ = "dev"

app = FastAPI(title="AutoGLM-GUI API", version=__version__)

# CORS 配置 (开发环境需要)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局单例 agent
agent: PhoneAgent | None = None

# 默认配置 (由 __main__.py 设置)
DEFAULT_BASE_URL: str = ""
DEFAULT_MODEL_NAME: str = "autoglm-phone-9b"


# 请求/响应模型
class InitRequest(BaseModel):
    base_url: str | None = None
    model_name: str | None = None
    device_id: str | None = None
    max_steps: int = 100


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    result: str
    steps: int
    success: bool


class StatusResponse(BaseModel):
    version: str
    initialized: bool
    step_count: int


class ScreenshotRequest(BaseModel):
    device_id: str | None = None


class ScreenshotResponse(BaseModel):
    success: bool
    image: str  # base64 encoded PNG
    width: int
    height: int
    is_sensitive: bool
    error: str | None = None


# API 端点
@app.post("/api/init")
async def init_agent(request: InitRequest) -> dict:
    """初始化 PhoneAgent。"""
    global agent

    # 使用请求参数或默认值
    base_url = request.base_url or DEFAULT_BASE_URL
    model_name = request.model_name or DEFAULT_MODEL_NAME

    if not base_url:
        raise HTTPException(
            status_code=400, detail="base_url is required"
        )

    model_config = ModelConfig(
        base_url=base_url,
        model_name=model_name,
    )

    agent_config = AgentConfig(
        max_steps=request.max_steps,
        device_id=request.device_id,
        verbose=True,
    )

    agent = PhoneAgent(
        model_config=model_config,
        agent_config=agent_config,
    )

    return {"success": True, "message": "Agent initialized"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """发送任务给 Agent 并执行。"""
    global agent

    if agent is None:
        raise HTTPException(
            status_code=400, detail="Agent not initialized. Call /api/init first."
        )

    try:
        result = agent.run(request.message)
        steps = agent.step_count
        agent.reset()

        return ChatResponse(result=result, steps=steps, success=True)
    except Exception as e:
        return ChatResponse(result=str(e), steps=0, success=False)


@app.get("/api/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """获取 Agent 状态和版本信息。"""
    global agent

    return StatusResponse(
        version=__version__,
        initialized=agent is not None,
        step_count=agent.step_count if agent else 0,
    )


@app.post("/api/reset")
async def reset_agent() -> dict:
    """重置 Agent 状态。"""
    global agent

    if agent is not None:
        agent.reset()

    return {"success": True, "message": "Agent reset"}


@app.post("/api/screenshot", response_model=ScreenshotResponse)
async def take_screenshot(request: ScreenshotRequest) -> ScreenshotResponse:
    """获取设备截图。此操作无副作用，不影响 PhoneAgent 运行。"""
    try:
        screenshot = get_screenshot(device_id=request.device_id)
        return ScreenshotResponse(
            success=True,
            image=screenshot.base64_data,
            width=screenshot.width,
            height=screenshot.height,
            is_sensitive=screenshot.is_sensitive,
        )
    except Exception as e:
        return ScreenshotResponse(
            success=False,
            image="",
            width=0,
            height=0,
            is_sensitive=False,
            error=str(e),
        )


# 静态文件托管 - 使用包内资源定位
def _get_static_dir() -> Path | None:
    """获取静态文件目录路径。"""
    try:
        # 尝试从包内资源获取
        static_dir = files("AutoGLM_GUI").joinpath("static")
        if hasattr(static_dir, "_path"):
            # Traversable 对象
            path = Path(str(static_dir))
            if path.exists():
                return path
        # 直接转换为 Path
        path = Path(str(static_dir))
        if path.exists():
            return path
    except (TypeError, FileNotFoundError):
        pass

    return None


STATIC_DIR = _get_static_dir()

if STATIC_DIR is not None and STATIC_DIR.exists():
    # 托管静态资源
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # 所有非 API 路由返回 index.html (支持前端路由)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:
        """Serve the SPA for all non-API routes."""
        # 如果请求的是具体文件且存在，则返回该文件
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        # 否则返回 index.html (支持前端路由)
        return FileResponse(STATIC_DIR / "index.html")
