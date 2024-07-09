from fastapi import APIRouter, Depends

from api.admin.contexts import admin_users, general_admin, search, users, companies
from api.admin.middleware import verify_admin_user

admin_router = APIRouter(prefix="/admin", dependencies=[Depends(verify_admin_user)])

admin_router.include_router(admin_users.router)
admin_router.include_router(general_admin.router)
admin_router.include_router(search.router)
admin_router.include_router(users.router)
admin_router.include_router(companies.router)