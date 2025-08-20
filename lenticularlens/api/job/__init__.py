from uuid import uuid4
from typing import Annotated
from fastapi import APIRouter, Form, Depends

from lenticularlens.api import oauth
from lenticularlens.api.job.instance import router as job_instance_router
from lenticularlens.api.dependencies import authenticated, UserDep

from lenticularlens.job.job import Job

from lenticularlens.util.hasher import hash_string
from lenticularlens.util.db_functions import get_all_jobs

router = APIRouter(prefix='/job', tags=['jobs'], dependencies=[Depends(authenticated)])
router.include_router(job_instance_router)


@router.get('')
async def list(user: UserDep):
    return user.list_jobs() if oauth and user else get_all_jobs()


@router.post('')
async def create(user: UserDep, job_title: Annotated[str, Form()],
                 job_description: Annotated[str, Form()], job_link: Annotated[str, Form()] = None):
    job_id = hash_string(job_title + job_description)
    job = Job(job_id)

    created = False
    while not created:
        try:
            job.create_job(job_title, job_description, job_link)
            created = True
        except:
            job_id = hash_string(uuid4().hex)
            job = Job(job_id)

    if oauth and user:
        user.register_job(job_id, 'owner')

    return {'job_id': job_id}
