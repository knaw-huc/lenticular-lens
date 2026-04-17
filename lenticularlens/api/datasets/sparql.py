from fastapi import APIRouter, Form
from typing_extensions import Annotated

from lenticularlens.data.sparql.dataset import Dataset
from lenticularlens.data.sparql.entity_type import EntityType

router = APIRouter(prefix='/sparql', tags=['sparql'])


@router.get('')
def datasets(sparql_endpoint: str):
    return Dataset.get_datasets_for_sparql(sparql_endpoint)


@router.post('/load')
def load(sparql_endpoint: Annotated[str, Form()]):
    Dataset.load_datasets_for_sparql(sparql_endpoint)


@router.post('')
def download(sparql_endpoint: Annotated[str, Form()], entity_type_id: Annotated[str, Form()]):
    EntityType.start_download(sparql_endpoint, entity_type_id)


@router.get('/downloads')
def downloads():
    return Dataset.get_downloads()
