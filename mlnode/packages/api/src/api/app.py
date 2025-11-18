import asyncio
import os

from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from api.inference.manager import InferenceManager
from api.inference.routes import router as inference_router

from api.models.manager import ModelManager
from api.models.routes import router as models_router

from api.gpu.manager import GPUManager
from api.gpu.routes import router as gpu_router

from zeroband.service.manager import TrainManager
from zeroband.service.routes import router as train_router

from pow.service.manager import PowManager
from pow.service.routes import router as pow_router

from pow.service.delegation.server import DelegationManager
from pow.service.delegation.routes import router as delegation_router

from api.health import router as health_router

from api.service_management import (
    ServiceState,
    check_service_conflicts,
    API_PREFIX
)
from api.routes import router as api_router
from api.watcher import watch_managers
from api.proxy import ProxyMiddleware, start_vllm_proxy, stop_vllm_proxy, setup_vllm_proxy, start_backward_compatibility, stop_backward_compatibility


WATCH_INTERVAL = 2


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.service_state = ServiceState.STOPPED
    app.state.pow_manager = PowManager()
    app.state.inference_manager = InferenceManager()
    app.state.train_manager = TrainManager()
    app.state.model_manager = ModelManager()
    app.state.gpu_manager = GPUManager()

    # Initialize delegation manager with environment variables
    delegation_auth_token = os.getenv("DELEGATION_AUTH_TOKEN", "")
    delegation_max_sessions = int(os.getenv("DELEGATION_MAX_SESSIONS", "10"))
    app.state.delegation_manager = DelegationManager(
        auth_token=delegation_auth_token,
        max_sessions=delegation_max_sessions
    )

    await start_vllm_proxy()

    monitor_task = asyncio.create_task(
        watch_managers(
            app,
            [
                app.state.pow_manager,
                app.state.inference_manager,
                app.state.train_manager,
            ],
            interval=WATCH_INTERVAL
        )
    )

    yield

    if app.state.pow_manager.is_running():
        app.state.pow_manager.stop()
    if app.state.inference_manager.is_running():
        # Use async stop in async context to avoid blocking event loop
        await app.state.inference_manager._async_stop()
    if app.state.train_manager.is_running():
        app.state.train_manager.stop()

    # Stop delegation manager and cleanup sessions
    app.state.delegation_manager.stop()

    app.state.gpu_manager._shutdown_nvml()

    await stop_vllm_proxy()
    await stop_backward_compatibility()

    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)

app.include_router(health_router)

app.add_middleware(ProxyMiddleware)

app.include_router(
    pow_router,
    prefix=API_PREFIX,
    tags=["PoW"],
    dependencies=[Depends(check_service_conflicts)]
)

app.include_router(
    train_router,
    prefix=API_PREFIX,
    tags=["Train"],
    dependencies=[Depends(check_service_conflicts)]
)

app.include_router(
    inference_router,
    prefix=API_PREFIX,
    tags=["Inference"],
    dependencies=[Depends(check_service_conflicts)]
)

app.include_router(
    api_router,
    prefix=API_PREFIX,
    tags=["API"],
)

app.include_router(
    models_router,
    prefix=API_PREFIX + "/models",
    tags=["Models"],
)

app.include_router(
    gpu_router,
    prefix=API_PREFIX + "/gpu",
    tags=["GPU"],
)

app.include_router(
    delegation_router,
    prefix=API_PREFIX + "/delegation",
    tags=["Delegation"],
)
