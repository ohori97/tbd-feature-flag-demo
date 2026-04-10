import os
import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from azure.identity.aio import DefaultAzureCredential
from azure.appconfiguration.provider.aio import load

# Logging configuration
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

app_config = None
credential = None

def is_feature_enabled(config, feature_id):
    if not config: return False
    fm = config.get("feature_management", {})
    ffs = fm.get("feature_flags", [])
    for f in ffs:
        if f.get("id") == feature_id:
            return f.get("enabled", False)
    return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_config, credential
    endpoint = os.getenv("APP_CONFIG_ENDPOINT")
    conn_str = os.getenv("APP_CONFIG_CONNECTION_STRING")
    
    if conn_str:
        logger.info("Connecting using Connection String.")
        app_config = await load(connection_string=conn_str, feature_flag_enabled=True, feature_flag_refresh_enabled=True, refresh_on=["Sentinel"])
    elif endpoint:
        logger.info(f"Connecting to: {endpoint}")
        credential = DefaultAzureCredential()
        
        # RBAC propagation delay retry loop
        max_retries = 20
        for i in range(max_retries):
            try:
                app_config = await load(endpoint=endpoint, credential=credential, feature_flag_enabled=True, feature_flag_refresh_enabled=True, refresh_on=["Sentinel"])
                logger.info("Successfully loaded App Configuration via Managed Identity.")
                break
            except Exception as e:
                logger.warning(f"Attempt {i+1}/{max_retries} failed: {e}")
                if i == max_retries - 1:
                    logger.error("Final attempt failed. Exiting.")
                    raise
                await asyncio.sleep(10)
    
    yield
    if credential:
        await credential.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "ok", "info": "TBD Feature Flag Demo App"}

@app.get("/greet")
async def greet_endpoint():
    global app_config
    if app_config:
        try:
            await app_config.refresh()
        except Exception as e:
            logger.error(f"Refresh failed: {e}")
    
    enabled = is_feature_enabled(app_config, "GreetingFeature")
    return {"message": "🚀 Hello from the New Feature Flag System!" if enabled else "Hello, World!"}
