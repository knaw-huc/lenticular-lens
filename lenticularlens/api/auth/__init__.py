from os import environ
from fastapi import APIRouter, Depends

from starlette.requests import Request
from starlette.responses import RedirectResponse

from lenticularlens.api.oauth import oauth
from lenticularlens.api.dependencies import authenticated
from lenticularlens.job.user import User

router = APIRouter(tags=['auth'])


@router.get('/login')
async def login(request: Request, redirect: str = '/'):
    request.session['redirect'] = redirect
    redirect_uri = environ.get('APP_DOMAIN', 'http://localhost') + '/oidc_redirect'
    return await oauth.oidc.authorize_redirect(request, redirect_uri)


@router.get('/oidc_redirect')
async def oidc_redirect(request: Request):
    token = await oauth.oidc.authorize_access_token(request)
    userinfo = token.get('userinfo') \
        if 'nickname' in token.get('userinfo') and 'email' in token.get('userinfo') else \
        await oauth.oidc.userinfo(token=token)
    request.session['user'] = dict(userinfo)

    if 'persisted' not in request.session:
        user = User(request.session.get('user'))
        user.persist_data()
        request.session['persisted'] = True

    return RedirectResponse(url=request.session.get('redirect') if 'redirect' in request.session else '/')


@router.get('/userinfo', dependencies=[Depends(authenticated)])
async def user_info(request: Request):
    return request.session.get('user')
