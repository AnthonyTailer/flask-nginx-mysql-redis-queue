from flask import Blueprint, request

from app import db

bp = Blueprint('api', __name__)


def wants_json_response():
    return request.accept_mimetypes['application/json'] >= \
           request.accept_mimetypes['text/html']


@bp.app_errorhandler(404)
def not_found_error(error):
    if wants_json_response():
        return errors.error_response(404, 'URL não encontrada')


@bp.app_errorhandler(405)
def not_found_error(error):
    if wants_json_response():
        return errors.error_response(405, 'O método não é permitido para a URL requisitada')


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if wants_json_response():
        return errors.error_response(500, 'Sorry, algo de errado não esta certo')


from app.api import secret, auth, errors, users, patients
