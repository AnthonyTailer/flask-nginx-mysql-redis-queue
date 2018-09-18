# -*- coding: utf-8 -*-

import os
import redis
from flask import request, current_app
from flask_restful import Resource, reqparse, fields, marshal
from rq import Queue, Connection
from werkzeug.utils import secure_filename
from project.server.main.tasks import google_transcribe_audio
from project.server.main.helpers import generate_hash_from_filename, allowed_file
from flask_jwt_extended import (create_access_token, jwt_required, get_raw_jwt, get_jwt_identity)
from project.server.main.models import *

import logging

logger = logging.getLogger(__name__)

formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')

file_handler = logging.FileHandler('./project/server/logs/resources.log')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


# UserModel resources
class UserRegistration(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username', help='username é obrigatório', required=True)
    parser.add_argument('fullname', help='Nome completo é obrigatório', required=True)
    parser.add_argument('password', help='senha é obrigatório', required=True)
    parser.add_argument(
        'type', choices=('anonymous', 'therapist'),
        help='Erro: tipo de usuário é obrigatório e deve ser uma string válida',
        required=True
    )

    def post(self):
        data = self.parser.parse_args()

        if UserModel.find_by_username(data['username']):
            logger.warn('Usuário {} já existe'.format(data['username']))
            return {'message': 'Usuário {} já existe'.format(data['username'])}, 422

        try:
            if data['type'] in EnumType.__members__:
                user_type = EnumType[data['type']].__str__()
            else:
                user_type = EnumType.anonymous.__str__()
        except (Exception, KeyError, LookupError) as e:
            logger.error('Tipo de usuário inválido ERROR: {}'.format(e))
            return {'message': 'Tipo de usuário inválido'}

        new_user = UserModel(
            username=data['username'],
            fullname=data['fullname'],
            password=UserModel.generate_hash(data['password']),
            type=user_type
        )
        try:
            new_user.save_to_db()
            access_token = create_access_token(identity=data['username'], expires_delta=False)
            logger.info('Usuário {} criado com sucesso'.format(data['username']))
            return {
                       'message': 'Usuário {} criado com sucesso'.format(data['username']),
                       'access_token': access_token,
                       'login': 'api/login'
                   }, 201
        except Exception as e:
            logger.error('Error {}'.format(e))
            return {'message': 'Algo de errado não está certo'}, 500


class UserLogin(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username', help='username é obrigatório', required=True)
    parser.add_argument('password', help='senha é obrigatório', required=True)

    def post(self):

        data = self.parser.parse_args()
        current_user = UserModel.find_by_username(data['username'])

        if not current_user:
            return {'message': 'Usuário {} não existe'.format(data['username'])}

        if UserModel.verify_hash(data['password'], current_user.password):
            access_token = create_access_token(identity=data['username'], expires_delta=False)
            return {
                'message': 'Logado como {}'.format(current_user.username),
                'access_token': access_token,
                'info': 'api/user'
            }
        else:
            return {'message': 'Senha ou username incorretos'}, 401


class UserResetPassword(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('current_password', help='Senha atual é obrigatória', required=True)
    parser.add_argument('new_password', help='Nova senha é obrigatória', required=True)

    @jwt_required
    def post(self):
        username = get_jwt_identity()
        data = self.parser.parse_args()
        current_user = UserModel.find_by_username(username)

        if not current_user:
            return {'message': 'Usuário inexistente'.format(username)}
        if UserModel.verify_hash(data['current_password'], current_user.password):
            try:
                UserModel.change_password(username, data['new_password'])
                logger.info('Senha alterada com sucesso')
                try:
                    jti = get_raw_jwt()['jti']
                    revoked_token = RevokedTokenModel(jti=jti)
                    revoked_token.add()
                    return {
                               'message': 'Senha alterada com sucesso',
                           }, 200
                except Exception as e:
                    return {'message': 'Algo de errado não está certo, {}'.format(e)}, 500
            except Exception as e:
                logger.error('Error {}'.format(e))
                return {'message': 'Algo de errado não está certo'}, 500
        return {'message': 'A senha atual não está correta'}, 422


class UserLogoutAccess(Resource):

    @jwt_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.add()
            return {'message': 'O seu token de acesso foi revogado com sucesso'}
        except Exception as e:
            return {'message': 'Algo de errado não está certo, {}'.format(e)}, 500


class User(Resource):

    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        resource_fields = {
            'id': fields.Integer,
            'username': fields.String,
            'fullname': fields.String,
            'type': fields.String
        }
        return marshal(UserModel.find_by_username(current_user), resource_fields, envelope='data')

    @jwt_required
    def put(self):
        username = get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('username', help='username é obrigatório', required=True)
        parser.add_argument('fullname', help='Nome completo é obrigatório', required=True)
        parser.add_argument(
            'type', choices=('anonymous', 'therapist'),
            help='Erro: tipo de usuário é obrigatório e deve ser uma string válida',
            required=True
        )
        data = parser.parse_args()
        current_user = UserModel.find_by_username(username)
        new_user = UserModel.find_by_username(data['username'])

        if not current_user:
            return {'message': 'Usuário inexistente'.format(username)}

        if new_user:
            if (new_user.username != current_user.username) and (new_user.id != current_user.id):
                logger.warn('Usuário {} já existe'.format(data['username']))
                return {'message': 'Usuário {} já existe'.format(data['username'])}, 422

        try:
            current_user.update_to_db(data['username'], data['fullname'], data['type'])
            logger.info('Usuário alterada com sucesso')
            try:
                if data['username'].strip() != username.strip():
                    jti = get_raw_jwt()['jti']
                    revoked_token = RevokedTokenModel(jti=jti)
                    revoked_token.add()
                return {
                           'message': 'Usuário alterada com sucesso',
                       }, 200
            except Exception as e:
                return {'message': 'Algo de errado não está certo, {}'.format(e)}, 500
        except Exception as e:
            return {'message': 'Algo de errado não está certo, {}'.format(e)}, 500


# class AllUsers(Resource):
#
#     @jwt_required
#     def get(self):
#         return UserModel.return_all()
#
#     @jwt_required
#     def delete(self):
#         return UserModel.delete_all()


# WordModel resources
class Word(Resource):

    @jwt_required
    def get(self, word=None):
        if not word:
            return {'message': 'Palavra não encontrada'}, 404

        resource_fields = {
            'id': fields.Integer,
            'word': fields.String,
            'tip': fields.String,
            'transcription': fields.List(fields.String)
        }

        return marshal(WordModel.find_by_word(word), resource_fields, envelope='data')

    @jwt_required
    def put(self, word=None):
        current_word = WordModel.find_by_word(word)

        if not current_word:
            return {'message': 'Palavra não encontrada'}, 404

        parser = reqparse.RequestParser()
        parser.add_argument('word', help='palavra é obrigatório', required=True)
        parser.add_argument('tip')

        data = parser.parse_args()
        new_word = WordModel.find_by_word(data['word'])

        if new_word:
            if (new_word.word != current_word.word) and (new_word.id != current_word.id):
                logger.warn('Palavra {} já existe'.format(data['word']))
                return {'message': 'Palavra {} já existe'.format(data['word'])}

        try:
            current_word.update_to_db(word=data['word'], tip=data['tip'])

            logger.info('Palavra {} atualizada com sucesso'.format(data['word']))
            return {
                       'message': 'Palavra {} atualizada com sucesso'.format(data['word']),
                       'route': '/api/word/{}'.format(current_word.word)
                   }, 201
        except Exception as e:
            logger.error('Error {}'.format(e))
            return {'message': 'Algo de errado não está certo, não foi possível atualizar sua palavra'}, 500

    @jwt_required
    def delete(self, word=None):
        if not word:
            return {'message': 'Palavra não encontrada'}, 404

        try:
            WordModel.delete_by_word(word)
            logger.info('Palavra {} deletada com sucesso'.format(word))
            return {
                'message': 'Palavra {} deletada com sucesso'.format(word),
            }
        except Exception as e:
            logger.error('Error {}'.format(e))
            return {'message': 'Algo de errado não está certo, não foi possível deletar sua palavra'}, 500


class WordAll(Resource):
    @jwt_required
    def get(self):
        resource_fields = {
            'id': fields.Integer,
            'word': fields.String,
            'tip': fields.String,
            'transcription': fields.List(fields.String)
        }

        return marshal(WordModel.return_all(), resource_fields, envelope='data')


class WordRegistration(Resource):
    @jwt_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('word', help='palavra é obrigatório', required=True)
        parser.add_argument('tip')

        data = parser.parse_args()

        if WordModel.find_by_word(data['word']):
            logger.warn('Palavra {} já existe'.format(data['word']))
            return {'message': 'Palavra {} já existe'.format(data['word'])}

        new_word = WordModel(
            word=data['word'],
            tip=data['tip']
        )
        try:
            new_word.save_to_db()

            logger.info('Palavra {} criada com sucesso'.format(data['word']))
            return {
                       'message': 'Palavra {} criada com sucesso'.format(data['word']),
                       'route': '/api/word/{}'.format(new_word.word)
                   }, 201
        except Exception as e:
            logger.error('Error {}'.format(e))
            return {'message': 'Algo de errado não está certo, não foi possível cadastrar sua palavra'}, 500


# WordTranscriptionModel resources

class WordTranscription(Resource):

    @jwt_required
    def get(self, transcription_id=None):
        if not transcription_id:
            return {'message': 'Transcrição não encontrada'}

        transc = WordTranscriptionModel.find_by_transcription_id(transcription_id)

        if not transc:
            return {'message': 'Transcrição não encontrada'}, 404

        resource_fields = {
            'id': fields.Integer,
            'word': fields.String,
            'transcription': fields.String
        }

        return marshal(WordTranscriptionModel.find_by_transcription_id(transcription_id), resource_fields,
                       envelope='data')

    @jwt_required
    def put(self, transcription_id=None):
        if not transcription_id:
            return {'message': 'Transcrição não encontrada'}

        transc = WordTranscriptionModel.find_by_transcription_id(transcription_id)

        if not transc:
            return {'message': 'Transcrição não encontrada'}, 404

        parser = reqparse.RequestParser()
        parser.add_argument('transcription', help='transcrição é obrigatório', required=True)
        parser.add_argument('word', help='A palavra é obrigatório', required=True)

        data = parser.parse_args()

        word = WordModel.find_by_word(data['word'])

        if word is None:
            logger.warn('Palavra {} inexistente'.format(data['word']))
            return {'message': 'Palavra {} inexistente'.format(data['word'])}

        try:
            transc.update_to_db(word_id=word.id, transcription=data['transcription'])
            logger.info('Transcription {} atualizada com sucesso'.format(data['transcription']))
            return {
                       'message': 'Transcription {} atualizada com sucesso'.format(data['transcription']),
                       'route': '/api/transcription/{}'.format(transc.id)
                   }, 201
        except Exception as e:
            logger.error('Error {}'.format(e))
            return {'message': 'Algo de errado não está certo, não foi possível atualizar sua palavra'}, 500

    @jwt_required
    def delete(self, transcription_id=None):
        if not transcription_id:
            return {'message': 'Transcrição não encontrada'}

        transc = WordTranscriptionModel.find_by_transcription_id(transcription_id)

        if not transc:
            return {'message': 'Transcrição não encontrada'}, 404

        try:
            transc.delete_transcription()
            logger.info('Transcrição {} deletada com sucesso'.format(transc.transcription))
            return {
                'message': 'Transcrição {} deletada com sucesso'.format(transc.transcription),
            }
        except Exception as e:
            logger.error('Error {}'.format(e))
            return {'message': 'Algo de errado não está certo, não foi possível deletar sua Transcrição'}, 500


class WordTranscriptionRegistration(Resource):
    @jwt_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('transcription', help='transcrição é obrigatório', required=True)
        parser.add_argument('word', help='A palavra é obrigatório', required=True)

        data = parser.parse_args()

        word = WordModel.find_by_word(data['word'])

        if word is None:
            logger.warn('Palavra {} inexistente'.format(data['word']))
            return {'message': 'Palavra {} inexistente'.format(data['word'])}

        new_transcription = WordTranscriptionModel(
            word_id=word.id,
            transcription=str(data['transcription']).strip()
        )
        try:
            new_transcription.save_to_db()

            logger.info('Transcrição de {} criada com sucesso'.format(data['word']))
            return {
                       'message': 'Transcrição de {} criada com sucesso'.format(data['word']),
                       'route': '/api/transcription/{}'.format(new_transcription.id)
                   }, 201
        except Exception as e:
            logger.error('Error {}'.format(e))
            return {'message': 'Algo de errado não está certo, não foi possível cadastrar sua Transcrição'}, 500


class SecretResource(Resource):

    @jwt_required
    def get(self):
        return {
            'answer': 42
        }


## Tasks Resources

class TaskStatus(Resource):

    @jwt_required
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


## Audio tasks


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
                    generate_hash_from_filename(filename) + '.' + filename.rsplit('.', 1)[1].lower())
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
