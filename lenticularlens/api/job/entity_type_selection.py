from typing import Annotated
from fastapi import APIRouter, Query, Form
from fastapi.responses import PlainTextResponse

from lenticularlens.api.dependencies import JobEtsDep, PagingParams
from lenticularlens.util.helpers import get_string_from_sql

router = APIRouter(prefix='/{id:int}', tags=['entity_type_selection'])


class SampleParams(PagingParams):
    invert: bool = False


@router.post('')
async def sample(data: JobEtsDep, params: Annotated[SampleParams, Form()]):
    job, id = data
    return job.get_entity_type_selection_sample(
        id,
        sql_only=False,
        invert=params.invert,
        offset=params.offset,
        limit=params.limit
    )


@router.get('', response_class=PlainTextResponse)
async def sample_sql(data: JobEtsDep, params: Annotated[SampleParams, Query()]):
    job, id = data
    result = job.get_entity_type_selection_sample(
        id,
        sql_only=True,
        invert=params.invert,
        offset=params.offset,
        limit=params.limit
    )
    return get_string_from_sql(result)


@router.post('/totals')
async def totals(data: JobEtsDep):
    job, id = data
    return job.get_entity_type_selection_sample_total(id, sql_only=False)


@router.get('/totals', response_class=PlainTextResponse)
async def totals_sql(data: JobEtsDep):
    job, id = data
    result = job.get_entity_type_selection_sample_total(id, sql_only=True)
    return get_string_from_sql(result)
