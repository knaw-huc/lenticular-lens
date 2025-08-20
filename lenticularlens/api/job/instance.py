from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from lenticularlens.api.job.spec import router as job_spec_router
from lenticularlens.api.job.entity_type_selection import router as job_ets_router
from lenticularlens.api.dependencies import JobDep, UserDep

router = APIRouter(prefix='/{job_id}', tags=['job_instance'])
router.include_router(job_spec_router)
router.include_router(job_ets_router)


@router.get('')
async def data(job: JobDep, user: UserDep):
    if user and (not job.data['users'] or user.user_id not in job.data['users']):
        user.register_job(job.data['job_id'], 'shared')

    return {
        'job_id': job.data['job_id'],
        'job_title': job.data['job_title'],
        'job_description': job.data['job_description'],
        'job_link': job.data['job_link'],
        'entity_type_selections': job.data['entity_type_selections_form_data'],
        'linkset_specs': job.data['linkset_specs_form_data'],
        'lens_specs': job.data['lens_specs_form_data'],
        'views': job.data['views_form_data'],
        'created_at': job.data['created_at'],
        'updated_at': job.data['updated_at']
    }


@router.put('')
async def update(job: JobDep, request: Request):
    data = await request.json()
    entity_type_selections, linkset_specs, lens_specs, views, errors = job.update_data(data)

    if len(errors) > 0:
        return JSONResponse(
            content={
                'job_id': job.job_id,
                'errors': [str(error) for error in errors],
                'entity_type_selections': [entity_type_selection['id'] for entity_type_selection in
                                           entity_type_selections],
                'linkset_specs': [linkset_spec['id'] for linkset_spec in linkset_specs],
                'lens_specs': [lens_spec['id'] for lens_spec in lens_specs],
                'views': [[view['id'], view['type']] for view in views],
            },
            status_code=400
        )

    return {
        'job_id': job.job_id,
        'entity_type_selections': [entity_type_selection['id'] for entity_type_selection in entity_type_selections],
        'linkset_specs': [linkset_spec['id'] for linkset_spec in linkset_specs],
        'lens_specs': [lens_spec['id'] for lens_spec in lens_specs],
        'views': [[view['id'], view['type']] for view in views],
    }


@router.delete('')
def delete(job: JobDep):
    job.delete()


@router.get('/linksets')
async def linksets(job: JobDep):
    return job.linksets


@router.get('/lenses')
async def lenses(job: JobDep):
    return job.lenses


@router.get('/clusterings')
async def clusterings(job: JobDep):
    return job.clusterings
