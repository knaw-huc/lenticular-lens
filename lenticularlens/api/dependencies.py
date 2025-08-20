from os import environ
from pydantic import BaseModel
from typing import Annotated, Literal, List, Optional
from fastapi import HTTPException, Depends
from starlette.requests import Request

from lenticularlens.api.oauth import oauth
from lenticularlens.job.job import Job
from lenticularlens.job.user import User
from lenticularlens.job.validation import Validation


def authenticated(request: Request):
    if oauth and 'user' not in request.session:
        raise HTTPException(status_code=401, detail='Please login!')


def authenticated_user(request: Request) -> Optional[User]:
    if oauth and 'user' in request.session:
        return User(request.session.get('user'))
    return None


async def admin_task(request: Request):
    access_token = request.query_params.get('access_token') or (await request.form()).get('access_token')
    if access_token != environ.get('ADMIN_ACCESS_TOKEN'):
        raise HTTPException(status_code=401, detail='No access!')


def id_to_job(job_id: str) -> Job:
    job = Job(job_id)
    if not job.data:
        raise HTTPException(status_code=404, detail=f"Job with id '{job_id}' not found")
    return job


def ids_to_job_and_spec(id: int, type: Literal['linkset', 'lens'], job: Job = Depends(id_to_job)) -> tuple[
    Job, Literal['linkset', 'lens'], int]:
    spec = job.get_spec_by_id(id, type)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Spec with type '{type}' and id '{id}' not found")
    return job, type, id


def ids_to_job_and_ets(id: int, job: Job = Depends(id_to_job)) -> tuple[Job, int]:
    ets = job.get_entity_type_selection_by_id(id)
    if not ets:
        raise HTTPException(status_code=404, detail=f"Entity-type selection with id '{id}' not found")
    return job, id


UserDep = Annotated[Optional[User], Depends(authenticated_user)]
JobDep = Annotated[Job, Depends(id_to_job)]
JobEtsDep = Annotated[tuple[Job, int], Depends(ids_to_job_and_ets)]
JobSpecDep = Annotated[tuple[Job, Literal['linkset', 'lens'], int], Depends(ids_to_job_and_spec)]


class PagingParams(BaseModel):
    offset: int = 0
    limit: int | None = None


class BasicFilterParams(BaseModel):
    uris: List[str] = []
    cluster_ids: List[int] = []
    min: float = 0
    max: float = 1


class LinksFilterParams(BaseModel):
    apply_filters: bool = True


class ClustersFilterParams(BaseModel):
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    min_count: Optional[int] = None
    max_count: Optional[int] = None


class LinksPropertiesFilterParams(BaseModel):
    with_properties: Literal['none', 'single', 'multiple'] = 'multiple'


class LinksValidationFilterParams(BaseModel):
    valid: list[Literal['all', 'accepted', 'rejected', 'uncertain', 'unchecked', 'disputed']] = ['all']


class ClustersNodesFilterParams(BaseModel):
    include_nodes: bool = False


class DefaultSortParams(BaseModel):
    sort: Literal['asc', 'desc'] = 'asc'


class ClustersSortParams(BaseModel):
    sort: Optional[Literal['size_asc', 'size_desc', 'count_asc', 'count_desc']] = None


class SourceTargetParams(BaseModel):
    source: str
    target: str
