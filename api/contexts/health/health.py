from fastapi import APIRouter

import ajb
from ajb.config.settings import SETTINGS

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/check")
def ping():
    return "OK"


@router.get("/version")
def version():
    return {"api_version": SETTINGS.APP_VERSION, "ajb_version": ajb.__version__}
