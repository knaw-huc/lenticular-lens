from typing import Annotated, Literal
from fastapi import APIRouter, Depends, Form, UploadFile, HTTPException

from lenticularlens.mapping.mapping import Mapping
from lenticularlens.api.dependencies import authenticated

router = APIRouter(prefix='/mappings', tags=['mappings'], dependencies=[Depends(authenticated)])


@router.post('', status_code=201)
async def create(type: Annotated[Literal['jsonld'], Form()],
                 url: Annotated[str, Form()] = None, file: UploadFile = None):
    if not url and not file:
        raise HTTPException(status_code=400, detail='You must provide either an URL or upload a file')

    mapping_id = Mapping.add(type, url, file)

    return {'mapping_id': mapping_id}


@router.get('/{mapping_id:path}')
async def mapping(mapping_id: str):
    mapping = Mapping(mapping_id)
    return mapping.map
