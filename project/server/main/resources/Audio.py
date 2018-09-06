import os
import redis

from rq import Queue, Connection
from flask import request, current_app
from flask_restful import Resource, reqparse
from werkzeug.utils import secure_filename

from project.server.main.tasks import google_transcribe_audio
from project.server.main.helpers import generate_hash_from_filename, allowed_file

parser = reqparse.RequestParser()


class AudioTranscription(Resource):
    def post(self):
        if request.method == 'POST':

            if 'file' not in request.files:
                return {
                    'error': 'No file was send'
                }, 400

            print(request.files)
            audio = request.files['file']

            if audio.filename == '':
                return {
                    'error': 'No selected file'
                }, 400

            if audio and allowed_file(audio.filename):
                filename = secure_filename(audio.filename)

                full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(
                    generate_hash_from_filename(filename)+'.'+filename.rsplit('.', 1)[1].lower())
                )

                audio.save(full_path)

                with Connection(redis.from_url(current_app.config['REDIS_URL'])):
                    q = Queue()
                    task = q.enqueue(google_transcribe_audio, full_path)

                response_object = {
                    'status': 'success',
                    'data': {
                        'task_id': task.get_id(),
                        'url': 'api/task/' + str(task.get_id())
                    }
                }

                return response_object, 202