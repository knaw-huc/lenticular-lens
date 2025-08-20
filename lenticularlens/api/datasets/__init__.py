from fastapi import APIRouter, Depends

from lenticularlens.api.datasets import sparql, timbuctoo
from lenticularlens.api.dependencies import authenticated

router = APIRouter(prefix='/datasets', dependencies=[Depends(authenticated)])

router.include_router(sparql.router)
router.include_router(timbuctoo.router)
