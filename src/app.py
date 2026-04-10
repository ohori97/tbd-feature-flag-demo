import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from azure.identity.aio import DefaultAzureCredential
from azure.appconfiguration.provider.aio import load
from typing import Protocol

class GreetingService(Protocol):
    def greet(self) -> str:
        ...

class DefaultGreetingService:
    def greet(self) -> str:
        return "Hello, World!"

class NewGreetingService:
    def greet(self) -> str:
        return "🚀 Hello from the New Feature Flag System!"

app_config = None
credential = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_config, credential
    endpoint = os.getenv("APP_CONFIG_ENDPOINT")
    
    if endpoint:
        credential = DefaultAzureCredential()
        # Load configuration with feature flags and dynamic refresh enabled
        app_config = await load(
            endpoint=endpoint,
            credential=credential,
            feature_flag_enabled=True,
            feature_flag_refresh_enabled=True,
            refresh_on=[{"key": "Sentinel"}]
        )
    yield
    if credential:
        await credential.close()

app = FastAPI(lifespan=lifespan)

@app.get("/greet")
async def greet_endpoint():
    global app_config
    if app_config:
        # Check if the Sentinel key has changed, and if so, refresh the configuration
        await app_config.refresh()
        use_new_feature = app_config.get("GreetingFeature", False)
    else:
        # Fallback if no App Config is available (e.g. local testing without endpoint)
        use_new_feature = False

    # Branch by Abstraction
    service: GreetingService
    if use_new_feature:
        service = NewGreetingService()
    else:
        service = DefaultGreetingService()

    return {"message": service.greet()}
