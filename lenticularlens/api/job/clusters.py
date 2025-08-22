from typing import Annotated
from psycopg.errors import UniqueViolation
from fastapi import APIRouter, Form, Query, HTTPException
from fastapi.responses import PlainTextResponse

from lenticularlens.api.dependencies import JobSpecDep, BasicFilterParams, ClustersFilterParams, PagingParams, \
    LinksFilterParams, ClustersNodesFilterParams, LinksPropertiesFilterParams, ClustersSortParams
from lenticularlens.util.helpers import get_string_from_sql

router = APIRouter(prefix='/clusters', tags=['clusters'])


class ClustersParams(BasicFilterParams, LinksFilterParams, LinksPropertiesFilterParams, ClustersFilterParams,
                     ClustersNodesFilterParams, ClustersSortParams, PagingParams):
    pass


class ClustersTotalsParams(BasicFilterParams, LinksFilterParams, ClustersFilterParams):
    pass


@router.post('')
async def clusters(data: JobSpecDep, params: Annotated[ClustersParams, Form()]):
    job, type, id = data
    return job.get_clusters(
        id, type,
        sql_only=False,
        cluster_ids=params.cluster_ids,
        uris=params.uris,
        min_strength=params.min,
        max_strength=params.max,
        min_size=params.min_size,
        max_size=params.max_size,
        min_count=params.min_count,
        max_count=params.max_count,
        sort=params.sort,
        limit=params.limit,
        offset=params.offset,
        with_view_properties=params.with_properties,
        with_view_filters=params.apply_filters,
        include_nodes=params.include_nodes,
    )


@router.get('', response_class=PlainTextResponse)
async def clusters_sql(data: JobSpecDep, params: Annotated[ClustersParams, Query()]):
    job, type, id = data
    result = job.get_clusters(
        id, type,
        sql_only=True,
        cluster_ids=params.cluster_ids,
        uris=params.uris,
        min_strength=params.min,
        max_strength=params.max,
        min_size=params.min_size,
        max_size=params.max_size,
        min_count=params.min_count,
        max_count=params.max_count,
        sort=params.sort,
        limit=params.limit,
        offset=params.offset,
        with_view_properties=params.with_properties,
        with_view_filters=params.apply_filters,
        include_nodes=params.include_nodes,
    )
    return get_string_from_sql(result)


@router.post('/totals')
async def totals(data: JobSpecDep, params: Annotated[ClustersTotalsParams, Form()]):
    job, type, id = data
    return job.get_clusters_totals(
        id, type,
        sql_only=False,
        cluster_ids=params.cluster_ids,
        uris=params.uris,
        min_strength=params.min,
        max_strength=params.max,
        with_view_filters=params.apply_filters,
        min_size=params.min_size,
        max_size=params.max_size,
        min_count=params.min_count,
        max_count=params.max_count,
    )


@router.get('/totals', response_class=PlainTextResponse)
async def totals_sql(data: JobSpecDep, params: Annotated[ClustersTotalsParams, Query()]):
    job, type, id = data
    result = job.get_clusters_totals(
        id, type,
        sql_only=True,
        cluster_ids=params.cluster_ids,
        uris=params.uris,
        min_strength=params.min,
        max_strength=params.max,
        with_view_filters=params.apply_filters,
        min_size=params.min_size,
        max_size=params.max_size,
        min_count=params.min_count,
        max_count=params.max_count,
    )
    return get_string_from_sql(result)


@router.post('/run')
async def run(data: JobSpecDep):
    try:
        job, type, id = data
        job.run_clustering(id, type)
    except UniqueViolation:
        raise HTTPException(status_code=400, detail=f'This {type} clustering already exists')


@router.post('/kill')
async def kill(data: JobSpecDep):
    job, type, id = data
    job.kill_clustering(id, type)
