from flask import jsonify
from app.api import bp
from app.api.auth import token_auth


@bp.route('/secret', methods=['GET'])
@token_auth.login_required
def secret():
    return jsonify({
        'answer': 42
    })
