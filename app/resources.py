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

# class UserResource(Resource):
#
#     @jwt_required
#     def get(self):
#         current_user = get_jwt_identity()
#         resource_fields = {
#             'id': fields.Integer,
#             'username': fields.String,
#             'fullname': fields.String,
#             'type': fields.String
#         }
#         return marshal(User.find_by_username(current_user), resource_fields, envelope='data')

#
#
# # Patient resources
#
# class PatientResource(Resource):
#     @jwt_required
#     def get(self, patient_id=None):
#         if not patient_id:
#             return {'message': 'Paciente não encontrado'}, 404
#
#         patient = Patient.find_by_id(patient_id)
#
#         if not patient:
#             return {'message': 'Paciente não encontrado'}, 404
#
#         resource_fields = {
#             'id': fields.Integer,
#             'name': fields.String,
#             'birth': fields.String,
#             'sex': fields.String,
#             'school': fields.String,
#             'school_type': fields.String,
#             'caregiver': fields.String,
#             'phone': fields.String,
#             'city': fields.String,
#             'state': fields.String,
#             'address': fields.String,
#         }
#         return marshal(patient, resource_fields, envelope='data')
#
#     @jwt_required
#     def put(self, patient_id):
#         if not patient_id:
#             return {'message': 'Paciente não encontrado'}, 404
#
#         patient = Patient.find_by_id(patient_id)
#
#         if not patient:
#             return {'message': 'Paciente não encontrado'}, 404
#
#         parser = reqparse.RequestParser(bundle_errors=True)
#         parser.add_argument('name', help='Nome completo é obrigatório', required=True)
#         parser.add_argument(
#             'birth',
#             help='Data de nascimento é obrigatória e deve estar no formato YYYY-mm-dd',
#             required=True,
#             type=inputs.date
#         )
#         parser.add_argument(
#             'sex',
#             choices=('M', 'F', ''),
#             help='Sexualidade deve ser um valor válido (M, F), ou não deve ser fornecida',
#             nullable=True,
#             required=False
#         )
#         parser.add_argument('school', help='Escola é obrigatória', required=True)
#         parser.add_argument(
#             'school_type',
#             choices=('PUB', 'PRI'),
#             help='Orgão escolar é obrigatório e deve ser uma string válida (PUB, PRI) ',
#             required=True
#         )
#         parser.add_argument('caregiver', nullable=True)
#         parser.add_argument('phone', nullable=True)
#         parser.add_argument('city', help="A Cidade é obrigatória", required=True)
#         parser.add_argument('state', help="O Estado é obrigatória", required=True)
#         parser.add_argument('address', nullable=True)
#
#         data = parser.parse_args()
#
#         try:
#             patient.update_to_db(
#                 data['name'], data['birth'], data['sex'], data['school'], data['school_type'], data['caregiver'],
#                 data['phone'], data['city'], data['state'], data['address']
#             )
#             current_app.logger.info('Paciente alterado com sucesso')
#             return {
#                        'message': 'Paciente {} alterado com sucesso'.format(data['name']),
#                        'info': 'api/pacient/{}'.format(patient.id)
#                    }, 200
#         except Exception as e:
#             current_app.logger.error('PUT PACIENT -> {}'.format(e))
#             return {'message': 'Algo de errado não está certo, {}'.format(e)}, 500
#
#
# class PatientAll(Resource):
#     @jwt_required
#     def get(self):
#         patients = Patient.return_all()
#
#         if not patients:
#             return {'message': 'Nenhum paciente não encontrado'}, 404
#
#         resource_fields = {
#             'id': fields.Integer,
#             'name': fields.String,
#             'birth': fields.String,
#             'sex': fields.String,
#             'school': fields.String,
#             'school_type': fields.String,
#             'caregiver': fields.String,
#             'phone': fields.String,
#             'city': fields.String,
#             'state': fields.String,
#             'address': fields.String,
#         }
#         return marshal(patients, resource_fields, envelope='data')
#
#
# # WordModel resources
# class WordResource(Resource):
#
#     @jwt_required
#     def get(self, word=None):
#         if not word:
#             return {'message': 'Palavra não encontrada'}, 404
#
#         resource_fields = {
#             'id': fields.Integer,
#             'word': fields.String,
#             'tip': fields.String,
#             'transcription': fields.List(fields.String)
#         }
#
#         return marshal(Word.find_by_word(word), resource_fields, envelope='data')
#
#     @jwt_required
#     def put(self, word=None):
#         current_word = Word.find_by_word(word)
#
#         if not current_word:
#             return {'message': 'Palavra não encontrada'}, 404
#
#         parser = reqparse.RequestParser(bundle_errors=True)
#         parser.add_argument('word', help='palavra é obrigatório', required=True)
#         parser.add_argument('tip')
#
#         data = parser.parse_args()
#         new_word = Word.find_by_word(data['word'])
#
#         if new_word:
#             if (new_word.word != current_word.word) and (new_word.id != current_word.id):
#                 current_app.logger.warn('Palavra {} já existe'.format(data['word']))
#                 return {'message': 'Palavra {} já existe'.format(data['word'])}
#
#         try:
#             current_word.update_to_db(word=data['word'], tip=data['tip'])
#
#             current_app.logger.info('Palavra {} atualizada com sucesso'.format(data['word']))
#             return {
#                        'message': 'Palavra {} atualizada com sucesso'.format(data['word']),
#                        'route': '/api/word/{}'.format(current_word.word)
#                    }, 201
#         except Exception as e:
#             current_app.logger.error('Error {}'.format(e))
#             return {'message': 'Algo de errado não está certo, não foi possível atualizar sua palavra'}, 500
#
#     @jwt_required
#     def delete(self, word=None):
#         if not word:
#             return {'message': 'Palavra não encontrada'}, 404
#
#         try:
#             Word.delete_by_word(word)
#             current_app.logger.info('Palavra {} deletada com sucesso'.format(word))
#             return {
#                 'message': 'Palavra {} deletada com sucesso'.format(word),
#             }
#         except Exception as e:
#             current_app.logger.error('Error {}'.format(e))
#             return {'message': 'Algo de errado não está certo, não foi possível deletar sua palavra'}, 500
#
#
# class WordAll(Resource):
#     @jwt_required
#     def get(self):
#         resource_fields = {
#             'id': fields.Integer,
#             'word': fields.String,
#             'tip': fields.String,
#             'transcription': fields.List(fields.String)
#         }
#
#         return marshal(Word.return_all(), resource_fields, envelope='data')
#
#
# class WordRegistration(Resource):
#     @jwt_required
#     def post(self):
#         parser = reqparse.RequestParser(bundle_errors=True)
#         parser.add_argument('word', help='palavra é obrigatório', required=True)
#         parser.add_argument('tip')
#
#         data = parser.parse_args()
#
#         if Word.find_by_word(data['word']):
#             current_app.logger.warn('Palavra {} já existe'.format(data['word']))
#             return {'message': 'Palavra {} já existe'.format(data['word'])}
#
#         new_word = Word(
#             word=data['word'],
#             tip=data['tip']
#         )
#         try:
#             new_word.save_to_db()
#
#             current_app.logger.info('Palavra {} criada com sucesso'.format(data['word']))
#             return {
#                        'message': 'Palavra {} criada com sucesso'.format(data['word']),
#                        'route': '/api/word/{}'.format(new_word.word)
#                    }, 201
#         except Exception as e:
#             current_app.logger.error('Error {}'.format(e))
#             return {'message': 'Algo de errado não está certo, não foi possível cadastrar sua palavra'}, 500
#
#
# # WordTranscriptionModel resources
# class WordTranscriptionResource(Resource):
#
#     @jwt_required
#     def get(self, transcription_id=None):
#         if not transcription_id:
#             return {'message': 'Transcrição não encontrada'}
#
#         transc = WordTranscription.find_by_transcription_id(transcription_id)
#
#         if not transc:
#             return {'message': 'Transcrição não encontrada'}, 404
#
#         resource_fields = {
#             'id': fields.Integer,
#             'word': fields.String,
#             'transcription': fields.String
#         }
#
#         return marshal(WordTranscription.find_by_transcription_id(transcription_id), resource_fields,
#                        envelope='data')
#
#     @jwt_required
#     def put(self, transcription_id=None):
#         if not transcription_id:
#             return {'message': 'Transcrição não encontrada'}
#
#         transc = WordTranscription.find_by_transcription_id(transcription_id)
#
#         if not transc:
#             return {'message': 'Transcrição não encontrada'}, 404
#
#         parser = reqparse.RequestParser(bundle_errors=True)
#         parser.add_argument('transcription', help='transcrição é obrigatório', required=True)
#         parser.add_argument('word', help='A palavra é obrigatório', required=True)
#
#         data = parser.parse_args()
#
#         word = Word.find_by_word(data['word'])
#
#         if word is None:
#             current_app.logger.warn('Palavra {} inexistente'.format(data['word']))
#             return {'message': 'Palavra {} inexistente'.format(data['word'])}
#
#         try:
#             transc.update_to_db(word_id=word.id, transcription=data['transcription'])
#             current_app.logger.info('Transcription {} atualizada com sucesso'.format(data['transcription']))
#             return {
#                        'message': 'Transcription {} atualizada com sucesso'.format(data['transcription']),
#                        'route': '/api/transcription/{}'.format(transc.id)
#                    }, 201
#         except Exception as e:
#             current_app.logger.error('Error {}'.format(e))
#             return {'message': 'Algo de errado não está certo, não foi possível atualizar sua palavra'}, 500
#
#     @jwt_required
#     def delete(self, transcription_id=None):
#         if not transcription_id:
#             return {'message': 'Transcrição não encontrada'}
#
#         transc = WordTranscription.find_by_transcription_id(transcription_id)
#
#         if not transc:
#             return {'message': 'Transcrição não encontrada'}, 404
#
#         try:
#             transc.delete_transcription()
#             current_app.logger.info('Transcrição {} deletada com sucesso'.format(transc.transcription))
#             return {
#                 'message': 'Transcrição {} deletada com sucesso'.format(transc.transcription),
#             }
#         except Exception as e:
#             current_app.logger.error('Error {}'.format(e))
#             return {'message': 'Algo de errado não está certo, não foi possível deletar sua Transcrição'}, 500
#
#
# class WordTranscriptionRegistration(Resource):
#     @jwt_required
#     def post(self):
#         parser = reqparse.RequestParser(bundle_errors=True)
#         parser.add_argument('transcription', help='transcrição é obrigatório', required=True)
#         parser.add_argument('word', help='A palavra é obrigatório', required=True)
#
#         data = parser.parse_args()
#
#         word = Word.find_by_word(data['word'])
#
#         if word is None:
#             current_app.logger.warn('Palavra {} inexistente'.format(data['word']))
#             return {'message': 'Palavra {} inexistente'.format(data['word'])}
#
#         new_transcription = WordTranscription(
#             word_id=word.id,
#             transcription=str(data['transcription']).strip()
#         )
#         try:
#             new_transcription.save_to_db()
#
#             current_app.logger.info('Transcrição de {} criada com sucesso'.format(data['word']))
#             return {
#                        'message': 'Transcrição de {} criada com sucesso'.format(data['word']),
#                        'route': '/api/transcription/{}'.format(new_transcription.id)
#                    }, 201
#         except Exception as e:
#             current_app.logger.error('Error {}'.format(e))
#             return {'message': 'Algo de errado não está certo, não foi possível cadastrar sua Transcrição'}, 500
#
#
# # Evaluation Resources
# class EvaluationRegistration(Resource):
#     @jwt_required
#     def post(self):
#         parser = reqparse.RequestParser(bundle_errors=True)
#         parser.add_argument(
#             'type', choices=('R', 'N', 'F'),
#             help='Erro: tipo de avaliação é obrigatório e deve ser uma string válida (R,N,F)',
#             required=True
#         )
#         parser.add_argument('patient_id', help='Paciente é obrigatório', required=True)
#         data = parser.parse_args()
#
#         patient = Patient.find_by_id(data['patient_id'])
#
#         if not patient:
#             current_app.logger.warn('Paciente inexistente')
#             return {'message': 'Paciente inexistente'}, 422
#
#         username = get_jwt_identity()
#
#         current_user = User.find_by_username(username)
#
#         new_evaluation = Evaluation(
#             type=data['type'],
#             patient_id=patient.id,
#             evaluator_id=current_user.id,
#         )
#
#         try:
#             new_evaluation.save_to_db()
#
#             current_app.logger.info('Avaliação criada com sucesso')
#             return {
#                        'message': 'Avaliação criada com sucesso',
#                        'route': '/api/evaluation/{}'.format(new_evaluation.id)
#                    }, 201
#         except Exception as e:
#             current_app.logger.error('Error {}'.format(e))
#             return {
#                        'message': 'Algo de errado não está certo, não foi possível cadastrar sua Avaliação',
#                        'error': '{}'.format(e)
#                    }, 500
#
#
# class EvaluationResource(Resource):
#     @jwt_required
#     def get(self, evaluation_id=None):
#         if not evaluation_id:
#             return {'message': 'Avaliação não encontrada'}, 404
#
#         evaluation = Evaluation.find_by_id(evaluation_id)
#
#         if not evaluation:
#             return {'message': 'Avaliação não encontrada'}, 404
#
#         resource_fields = {
#             'id': fields.Integer,
#             'date': fields.String,
#             'type': fields.String,
#             'patient': fields.String,
#             'patient_id': fields.Integer,
#             'evaluator': fields.String,
#             'evaluator_id': fields.Integer
#         }
#         return marshal(evaluation, resource_fields, envelope='data')
#
#     @jwt_required
#     def put(self, evaluation_id):
#         if not evaluation_id:
#             return {'message': 'Avaliação não encontrada'}, 404
#
#         evaluation = Evaluation.find_by_id(evaluation_id)
#
#         if not evaluation:
#             return {'message': 'Avaliação não encontrada'}, 404
#
#         parser = reqparse.RequestParser(bundle_errors=True)
#         parser.add_argument(
#             'type', choices=('R', 'N', 'F'),
#             help='Erro: tipo de avaliação é obrigatório e deve ser uma string válida (R,N,F)',
#             required=True
#         )
#         parser.add_argument('patient_id', help='Paciente é obrigatório', required=True, type=fields.Integer)
#         data = parser.parse_args()
#
#         try:
#             evaluation.update_to_db(type=data['type'], patient_id=data['patient_id'])
#             current_app.logger.info('Avaliação alterada com sucesso')
#             return {
#                        'message': 'Avaliação alterada com sucesso',
#                        'info': 'api/pacient/{}'.format(evaluation.id)
#                    }, 200
#         except Exception as e:
#             current_app.logger.error('PUT EVALUATION -> {}'.format(e))
#             return {'message': 'Algo de errado não está certo, {}'.format(e)}, 500
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