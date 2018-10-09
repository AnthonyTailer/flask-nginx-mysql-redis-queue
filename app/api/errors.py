from flask import jsonify, current_app
from werkzeug.http import HTTP_STATUS_CODES


def error_response(status_code, message=None):
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Erro desconhecido')}
    if message:
        payload['message'] = message
        current_app.logger.warn(message)
    response = jsonify(payload)
    response.status_code = status_code
    return response


def bad_request(message):
    return error_response(400, message)