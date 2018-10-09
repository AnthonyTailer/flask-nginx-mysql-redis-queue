from flask import jsonify, request, url_for
from flask_jwt_extended import jwt_required
from app.api import bp


# from app.api.auth import token_auth
# from app.api.errors import bad_request

@bp.route('/secret', methods=['GET'])
@jwt_required
def secret():
    return jsonify({
        'answer': 42
    })
