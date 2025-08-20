from os import environ
from authlib.integrations.starlette_client import OAuth

oauth = None
if 'OIDC_SERVER' in environ and len(environ['OIDC_SERVER']) > 0:
    oauth = OAuth()
    oauth.register(
        name='oidc',
        client_id=environ['OIDC_CLIENT_ID'],
        client_secret=environ['OIDC_CLIENT_SECRET'],
        server_metadata_url=environ['OIDC_SERVER'] + '/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid profile email'
        }
    )
