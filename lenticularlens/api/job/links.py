from typing import Annotated
from psycopg.errors import UniqueViolation
from fastapi import APIRouter, Form, Query, HTTPException
from fastapi.responses import PlainTextResponse

from lenticularlens.job.lens_sql import LensSql
from lenticularlens.job.matching_sql import MatchingSql
from lenticularlens.job.validation import Validation
from lenticularlens.api.dependencies import JobSpecDep, BasicFilterParams, PagingParams, LinksFilterParams, \
    LinksValidationFilterParams, LinksPropertiesFilterParams, DefaultSortParams
from lenticularlens.util.helpers import get_string_from_sql

router = APIRouter(prefix='/links', tags=['links'])


class LinksParams(BasicFilterParams, LinksFilterParams, LinksPropertiesFilterParams,
                  LinksValidationFilterParams, DefaultSortParams, PagingParams):
    pass


class LinksTotalsParams(BasicFilterParams, LinksFilterParams):
    pass


@router.post('')
async def links(data: JobSpecDep, params: Annotated[LinksParams, Form()]):
    job, type, id = data
    return job.get_links(
        id, type,
        sql_only=False,
        validation_filter=Validation.get(params.valid),
        cluster_ids=params.cluster_ids,
        uris=params.uris,
        min_strength=params.min,
        max_strength=params.max,
        sort=params.sort,
        limit=params.limit,
        offset=params.offset,
        with_view_properties=params.with_properties,
        with_view_filters=params.apply_filters,
    )


@router.get('', response_class=PlainTextResponse)
async def links_sql(data: JobSpecDep, params: Annotated[LinksParams, Query()]):
    job, type, id = data
    result = job.get_links(
        id, type,
        sql_only=True,
        validation_filter=Validation.get(params.valid),
        cluster_ids=params.cluster_ids,
        uris=params.uris,
        min_strength=params.min,
        max_strength=params.max,
        sort=params.sort,
        limit=params.limit,
        offset=params.offset,
        with_view_properties=params.with_properties,
        with_view_filters=params.apply_filters,
    )
    return get_string_from_sql(result)


@router.get('/sql')
async def sql(data: JobSpecDep):
    job, type, id = data
    job_sql = MatchingSql(job, id) if type == 'linkset' else LensSql(job, id)
    return job_sql.sql_string


@router.post('/run')
async def run(data: JobSpecDep, restart: Annotated[bool, Form()] = False):
    try:
        job, type, id = data
        job.run_linkset(id, restart) if type == 'linkset' else job.run_lens(id, restart)
    except UniqueViolation:
        raise HTTPException(status_code=400, detail=f'This {type} already exists')


@router.post('/kill')
async def kill(data: JobSpecDep):
    job, type, id = data
    job.kill_linkset(id) if type == 'linkset' else job.kill_lens(id)


@router.post('/totals')
async def totals(data: JobSpecDep, params: Annotated[LinksTotalsParams, Form()]):
    job, type, id = data
    return job.get_links_totals(
        id, type,
        sql_only=False,
        cluster_ids=params.cluster_ids,
        uris=params.uris,
        min_strength=params.min,
        max_strength=params.max,
        with_view_filters=params.apply_filters
    )


@router.get('/totals', response_class=PlainTextResponse)
async def totals_sql(data: JobSpecDep, params: Annotated[LinksTotalsParams, Query()]):
    job, type, id = data
    result = job.get_links_totals(
        id, type,
        sql_only=True,
        cluster_ids=params.cluster_ids,
        uris=params.uris,
        min_strength=params.min,
        max_strength=params.max,
        with_view_filters=params.apply_filters
    )
    return get_string_from_sql(result)
