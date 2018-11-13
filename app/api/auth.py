from flask import g, abort
from flask_httpauth import HTTPTokenAuth
from app.models import User, EnumType
from app.api.errors import error_response
from functools import wraps

token_auth = HTTPTokenAuth()


@token_auth.verify_token
def verify_token(token):
    g.current_user = User.check_token(token) if token else None
    return g.current_user is not None


@token_auth.error_handler
def token_auth_error():
    return error_response(401, 'URL não autorizada, faça login para ter acesso')


def only_therapist(func):
    """Verifica de o usuário logado é do tipo Therapist, retornando erro 401 caso não seja"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not g.current_user.type == EnumType.therapist.__str__():
            abort(403)
        return func(*args, **kwargs)

    return wrapper


def only_anonymous(func):
    """ Verifica de o usuário logado é do tipo anonymous, retornando erro 401 caso não seja"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not g.current_user.type == EnumType.anonymous.__str__():
            abort(403)
        return func(*args, **kwargs)

    return wrapper
