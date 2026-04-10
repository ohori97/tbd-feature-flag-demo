import os, asyncio, logging, sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from azure.identity.aio import DefaultAzureCredential
from azure.appconfiguration.provider.aio import load

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

app_config = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_config
    conn_str = os.getenv("APP_CONFIG_CONNECTION_STRING")
    if conn_str:
        app_config = await load(connection_string=conn_str, feature_flag_enabled=True, feature_flag_refresh_enabled=True, refresh_on=["Sentinel"])
    yield

app = FastAPI(lifespan=lifespan)
@app.get("/greet")
async def greet():
    global app_config
    if app_config: await app_config.refresh()
    
    fm = app_config.get("feature_management", {})
    enabled = False
    for f in fm.get("feature_flags", []):
        if f.get("id") == "GreetingFeature":
            enabled = f.get("enabled", False)
            break
    
    return {"message": "🚀 Hello from the New Feature Flag System!" if enabled else "Hello, World!"}
