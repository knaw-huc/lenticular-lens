from typing import Annotated, Literal, Optional
from fastapi import APIRouter, HTTPException, Form, Query
from starlette.responses import StreamingResponse

from lenticularlens.job.validation import Validation
from lenticularlens.job.export import CsvExport, RdfExport
from lenticularlens.api.job.links import router as links_router
from lenticularlens.api.job.clusters import router as clusters_router
from lenticularlens.api.dependencies import JobSpecDep, LinksValidationFilterParams, BasicFilterParams, \
    LinksFilterParams, SourceTargetParams, UserDep

router = APIRouter(prefix='/{type}/{id:int}', tags=['spec'])
router.include_router(links_router)
router.include_router(clusters_router)


class RdfExportParams(LinksValidationFilterParams):
    export_linkset: bool = True
    export_metadata: bool = True
    export_validation_set: bool = True
    export_cluster_set: bool = True
    reification: Literal['none', 'standard', 'singleton', 'rdf_star'] = 'none'
    link_pred_namespace: Optional[str] = None
    link_pred_shortname: Optional[str] = None
    creator: Optional[str] = None


class ValidationParams(BasicFilterParams, SourceTargetParams, LinksFilterParams, LinksValidationFilterParams):
    validation: Literal['all', 'accepted', 'rejected', 'uncertain', 'unchecked', 'disputed'] = 'all'


class MotivationParams(BasicFilterParams, SourceTargetParams, LinksFilterParams, LinksValidationFilterParams):
    motivation: str


@router.delete('')
def delete(data: JobSpecDep):
    job, type, id = data
    lens_uses = job.spec_lens_uses(id, type)
    if len(lens_uses) > 0:
        raise HTTPException(status_code=400, detail=f'There are dependencies on lenses {lens_uses}')

    job.delete_spec(id, type)


@router.post('/validate')
def validate(data: JobSpecDep, params: Annotated[ValidationParams, Form()]):
    job, type, id = data
    job.validate_link(
        id, type, params.validation,
        validation_filter=Validation.get(params.valid),
        cluster_ids=params.cluster_ids,
        uris=params.uris,
        min_strength=params.min,
        max_strength=params.max,
        link=(params.source, params.target),
        with_view_filters=params.apply_filters
    )


@router.post('/motivate')
def motivate(data: JobSpecDep, params: Annotated[MotivationParams, Form()]):
    job, type, id = data
    job.motivate_link(
        id, type, params.motivation,
        validation_filter=Validation.get(params.valid),
        cluster_ids=params.cluster_ids,
        uris=params.uris,
        min_strength=params.min,
        max_strength=params.max,
        link=(params.source, params.target),
        with_view_filters=params.apply_filters
    )


@router.get('/cluster/{cluster_id}/graph')
def cluster_graph_data(data: JobSpecDep, cluster_id: int):
    job, type, id = data
    return job.visualize(id, type, cluster_id)


@router.get('/csv')
def csv_export(data: JobSpecDep, params: Annotated[LinksValidationFilterParams, Query()]):
    job, type, id = data
    export = CsvExport(job, type, id)
    export_generator = export.create_generator(Validation.get(params.valid))

    return StreamingResponse(
        export_generator,
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename={type}_{job.job_id}_{str(id)}.csv'}
    )


@router.get('/rdf')
def rdf_export(data: JobSpecDep, user: UserDep, params: Annotated[RdfExportParams, Query()]):
    job, type, id = data
    export = RdfExport(job, type, id)
    export_generator = export.create_generator(
        link_pred_namespace=params.link_pred_namespace,
        link_pred_shortname=params.link_pred_shortname,
        export_linkset=params.export_linkset,
        export_metadata=params.export_metadata,
        export_validation_set=params.export_validation_set,
        export_cluster_set=params.export_cluster_set,
        reification=params.reification,
        creator=user.name if user else params.creator,
        validation_filter=Validation.get(params.valid)
    )

    use_graphs = ((params.export_linkset and
                   params.export_metadata or params.export_validation_set or params.export_cluster_set) or
                  params.export_validation_set or params.export_cluster_set)
    mimetype = 'application/trig' if use_graphs else 'text/turtle'
    extension = 'trig' if use_graphs else 'ttl'

    return StreamingResponse(
        export_generator,
        media_type=mimetype,
        headers={'Content-Disposition': f'attachment; filename={type}_{job.job_id}_{str(id)}.{extension}'}
    )
