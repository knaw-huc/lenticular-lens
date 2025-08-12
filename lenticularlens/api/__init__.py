from os import environ
from uuid import uuid4

from fastapi import FastAPI
from socketio import ASGIApp
from brotli_asgi import BrotliMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from lenticularlens.api.oauth import oauth
from lenticularlens.api.auth import router as auth_router
from lenticularlens.api.socket import sio, fastapi_lifespan
from lenticularlens.api.utils import router as utils_router
from lenticularlens.api.datasets import router as datasets_router
from lenticularlens.api.mappings import router as mappings_router
from lenticularlens.api.job import router as job_router
from lenticularlens.api.admin import router as admin_router
from lenticularlens.util.config_logging import config_logger

config_logger()

app = FastAPI(lifespan=fastapi_lifespan)
app.mount('/socket.io', ASGIApp(sio))

app.add_middleware(BrotliMiddleware)
app.add_middleware(SessionMiddleware, secret_key=environ.get('SECRET_KEY', uuid4().hex))
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

if oauth:
    app.include_router(auth_router)

app.include_router(utils_router)
app.include_router(datasets_router)
app.include_router(mappings_router)
app.include_router(job_router)
app.include_router(admin_router)
