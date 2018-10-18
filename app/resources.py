# # -*- coding: utf-8 -*-
# import os
# import redis
# from datetime import datetime
#
# from flask import current_app
#
# import werkzeug
# from flask_restful import Resource, reqparse, fields, marshal, inputs
# from flask.views import MethodView
# from rq import Queue, Connection
# from werkzeug.utils import secure_filename
# from app.helpers import generate_hash_from_filename, allowed_file
# from flask_jwt_extended import (create_access_token, jwt_required, get_raw_jwt, get_jwt_identity)
#
# from app.models import User, Evaluation, Patient, WordTranscription, \
#     Word, WordEvaluation, RevokedToken, EnumType
# from app.tasks import ml_transcribe_audio

#
#
# class WordEvaluationRegistration(Resource):
#     @jwt_required
#     def post(self):
#         parser = reqparse.RequestParser(bundle_errors=True)
#         parser.add_argument(
#             'audio',
#             type=werkzeug.datastructures.FileStorage,
#             location='files',
#             required=True,
#             help="O audio é obrigatório"
#         )
#         parser.add_argument('evaluation_id', required=True, help="A avaliação é obrigatória")
#         parser.add_argument('word', required=True, help="A palavra é obrigatória")
#         parser.add_argument(
#             'transcription_target_id',
#             required=True,
#             help="A transcrição alvo é obrigatória"
#         )
#         parser.add_argument('repetition', type=fields.Boolean, help="Foi utilizado o método de repetição?")
#         parser.add_argument('transcription_eval', help="A transcrição identificada deve ser fornecida")
#
#         data = parser.parse_args()
#
#         evaluation = Evaluation.find_by_id(data['evaluation_id'])
#
#         if not evaluation:
#             return {'message': 'Avaliação não encontrada'}, 404
#
#         word = Word.find_by_word(data['word'])
#
#         if not word:
#             return {'message': 'Palavra não encontrada'}, 404
#
#         target_transc = WordTranscription.find_by_transcription_id(data['transcription_target_id'])
#
#         if not target_transc:
#             return {'message': 'Transcrição alvo não encontrada'}, 404
#
#         if data['audio'] and allowed_file(data['audio'].filename):
#             filename = secure_filename(data['audio'].filename)
#
#             full_path = os.path.join(
#                 current_app.config['UPLOAD_FOLDER'],
#                 str(generate_hash_from_filename(filename) + '.' + filename.rsplit('.', 1)[1].lower())
#             )
#
#             try:
#                 data['audio'].save(full_path)
#             except Exception as e:
#                 current_app.logger.error('POST WORD_EVALUATION  SAVE AUDIO -> {}'.format(e))
#                 return {'message': 'Algo de errado não está certo, {}'.format(e)}, 500
#             else:
#
#                 new_word_eval = WordEvaluation(
#                     evaluation_id=evaluation.id,
#                     word_id=word.id,
#                     transcription_target_id=target_transc.id,
#                     transcription_eval=data['transcription_eval'],
#                     repetition=data['repetition'],
#                     audio_path=full_path
#                 )
#
#                 try:
#
#
#                     username = get_jwt_identity()
#                     current_user = User.find_by_username(username)
#
#                     new_word_eval.save_to_db()
#
#                     # current_app.logger.info('Avaliação do audio criada com sucesso')
#                     # task1 = q.enqueue(new_word_eval.google_transcribe_audio, full_path)
#                     #  GOOGLE API AUDIO EVALUATION
#
#                     # ML AUDIO EVALUATION
#                     task2 = current_user.lanch_task('ml_transcribe_audio', 'Audio Evaluation', new_word_eval.evaluation_id, new_word_eval.word_id,
#                                       data['word'], full_path)
#                     # job2 = task2.get_rq_job()
#                     # task2 = q.enqueue(current_app, ml_transcribe_audio, new_word_eval.evaluation_id, new_word_eval.word_id,
#                     #                   data['word'], full_path)
#                     return {
#                                'message': 'Avaliação do audio criada com sucesso',
#                                'data': {
#                                    # 'task_api_id': task1.get_id(),
#                                    # 'url_api': 'api/task/' + str(task1.get_id()),
#                                    'task_ml_id': task2.id,
#                                    'url_ml': 'api/task/' + str(task2.id),
#                                }
#                            }, 201
#                 except Exception as e:
#                     current_app.logger.error('POST WORD_EVALUATION -> {}'.format(e))
#                     return {'message': 'Algo de errado não está certo, {}'.format(e)}, 500
#         else:
#             return {
#                        'message': 'Arquivo de audio não permitido'
#                    }, 422
#
#
# # Tasks Resources
# class TaskStatus(Resource):
#
#     @jwt_required
#     def get(self, task_id):
#
#         with Connection(redis.from_url(current_app.config['REDIS_URL'])):
#             q = Queue()
#             task = q.fetch_job(task_id)
#         if task:
#             response_object = {
#                 'status': 'success',
#                 'data': {
#                     'task_id': task.get_id(),
#                     'task_status': task.get_status(),
#                     'task_result': task.result,
#                 }
#             }
#         else:
#             response_object = {'status': 'error'}
#         return response_object
#
#
# # class AudioTranscription(Resource):
# #     def post(self):
# #         if request.method == 'POST':
# #
# #             if 'file' not in request.files:
# #                 return {
# #                            'error': 'No file was send'
# #                        }, 400
# #
# #             print(request.files)
# #             audio = request.files['file']
# #
# #             if audio.filename == '':
# #                 return {
# #                            'error': 'No selected file'
# #                        }, 400
# #
# #             if audio and allowed_file(audio.filename):
# #                 filename = secure_filename(audio.filename)
# #
# #                 full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(
# #                     generate_hash_from_filename(filename) + '.' + filename.rsplit('.', 1)[1].lower())
# #                                          )
# #
# #                 audio.save(full_path)
# #
# #                 with Connection(redis.from_url(current_app.config['REDIS_URL'])):
# #                     q = Queue()
# #                     task = q.enqueue(google_transcribe_audio, full_path)
# #
# #                 response_object = {
# #                     'status': 'success',
# #                     'data': {
# #                         'task_id': task.get_id(),
# #                         'url': 'api/task/' + str(task.get_id())
# #                     }
# #                 }
# #
# #                 return response_object, 202
#
#
# class SecretResource(Resource):
#     @jwt_required
#     def get(self):
#         return {
#             'answer': 42
#         }