import redis

from rq import Queue, Connection
from flask import current_app
from flask_restful import Resource, reqparse

# @main_blueprint.route('/tasks', methods=['POST'])
# def run_task():
#     task_type = request.form['type']
#     with Connection(redis.from_url(current_app.config['REDIS_URL'])):
#         q = Queue()
#         task = q.enqueue(create_task, task_type)
#     response_object = {
#         'status': 'success',
#         'data': {
#             'task_id': task.get_id()
#         }
#     }
#     return jsonify(response_object), 202
#
#

class TaskStatus(Resource):

    def get(self):
        with Connection(redis.from_url(current_app.config['REDIS_URL'])):
            q = Queue()
            task = q.fetch_job(self.task_id)
        if task:
            response_object = {
                'status': 'success',
                'data': {
                    'task_id': task.get_id(),
                    'task_status': task.get_status(),
                    'task_result': task.result,
                }
            }
        else:
            response_object = {'status': 'error'}
        return response_object