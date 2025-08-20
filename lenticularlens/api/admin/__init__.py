from threading import Thread
from fastapi import APIRouter, Depends

from lenticularlens.api.dependencies import admin_task
from lenticularlens.util.admin_tasks import cleanup_jobs, cleanup_downloaded

router = APIRouter(prefix='/admin', tags=['admin'], dependencies=[Depends(admin_task)])


@router.post('/cleanup_jobs')
async def jobs_cleanup():
    Thread(target=cleanup_jobs).start()


@router.post('/cleanup_downloaded')
async def downloaded_cleanup():
    Thread(target=cleanup_downloaded).start()
