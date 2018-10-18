from app.api import bp
from flask import current_app, jsonify, g
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.models import Task


@bp.route('/task/<string:task_id>', methods=['GET'])
@token_auth.login_required
def get_task(task_id=None):
    if not task_id:
        return bad_request('Task não informada')
    user = g.current_user
    task = Task.get_task_by_user(task_id, user)

    if not task:
        return bad_request('Task não encontrada')

    return jsonify({'data': {
        'task_id': task.get_id(),
        'task_status': task.get_status(),
        'task_result': task.result,
    }}), 200
