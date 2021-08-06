# Overwrite of the decorator 'oidc_auth' from OIDCAuthentication from the package 'flask_pyoidc'.
# This to allow a custom destination URL.

from oic import rndstr
from flask import session as flask_session, redirect
from urllib.parse import parse_qsl
from flask_pyoidc.user_session import UserSession
from flask_pyoidc.auth_response_handler import AuthResponseHandler


def oidc_auth(auth, provider_name, destination='/'):
    def authenticate(client, interactive=True):
        if not client.is_registered():
            auth._register_client(client)

        flask_session['destination'] = destination

        extra_auth_params = {}
        if not interactive:
            extra_auth_params['prompt'] = 'none'

        auth_req = client.authentication_request(state=rndstr(), nonce=rndstr(), extra_auth_params=extra_auth_params)
        flask_session['auth_request'] = auth_req.to_json()
        login_url = client.login_url(auth_req)

        auth_params = dict(parse_qsl(login_url.split('?')[1]))
        flask_session['fragment_encoded_response'] = AuthResponseHandler.expect_fragment_encoded_response(auth_params)
        return redirect(login_url)

    session = UserSession(flask_session, provider_name)
    client = auth.clients[session.current_provider]

    if session.should_refresh(client.session_refresh_interval_seconds):
        return authenticate(client, interactive=False)
    elif session.is_authenticated():
        return redirect(destination)
    else:
        return authenticate(client)
