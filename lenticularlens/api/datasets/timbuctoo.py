from fastapi import APIRouter, Form
from typing_extensions import Annotated

from lenticularlens.data.timbuctoo.dataset import Dataset
from lenticularlens.data.timbuctoo.entity_type import EntityType

router = APIRouter(prefix='/timbuctoo', tags=['timbuctoo'])


@router.get('')
async def datasets(graphql_endpoint: str):
    return Dataset.get_datasets_for_graphql(graphql_endpoint)


@router.post('')
async def download(graphql_endpoint: Annotated[str, Form()], timbuctoo_id: Annotated[str, Form()],
                   entity_type_id: Annotated[str, Form()]):
    EntityType.start_download(graphql_endpoint, timbuctoo_id, entity_type_id)


@router.get('/downloads')
async def downloads():
    return Dataset.get_downloads()
