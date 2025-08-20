from fastapi import APIRouter, HTTPException, Depends

from lenticularlens.api.dependencies import authenticated
from lenticularlens.util.stopwords import get_stopwords
from lenticularlens.util.db_functions import get_filter_functions, get_matching_methods, get_transformers

router = APIRouter(tags=['utils'], dependencies=[Depends(authenticated)])

@router.get('/')
async def index():
    return 'Lenticular Lens'


@router.get('/stopwords/{dictionary}')
async def stopwords(dictionary: str):
    try:
        return get_stopwords(dictionary)
    except:
        raise HTTPException(status_code=400, detail='Please specify a valid dictionary key')


@router.get('/methods')
async def methods():
    filter_functions_info = get_filter_functions()
    matching_methods_info = get_matching_methods()
    transformers_info = get_transformers()

    return {
        'filter_functions': filter_functions_info,
        'filter_functions_order': list(filter_functions_info.keys()),
        'matching_methods': matching_methods_info,
        'matching_methods_order': list(matching_methods_info.keys()),
        'transformers': transformers_info,
        'transformers_order': list([key for key, item in transformers_info.items() if not item.get('internal', False)]),
    }
