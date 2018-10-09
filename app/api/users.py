from flask import request, jsonify
from flask_restful import marshal, fields

from app.models import User, EnumType, RevokedToken, UserSchema
from flask_jwt_extended import (create_access_token, jwt_required, get_raw_jwt, get_jwt_identity)
from app.api import bp
from flask import current_app
from app.api.errors import bad_request
from app import db


@bp.route('/registration', methods=['POST'])
def registration():
    data = request.get_json(silent=True) or {}
    if User.find_by_username(data['username']):
        return bad_request('Usuário {} já esta em uso'.format(data['username']))

    if 'username' not in data or 'fullname' not in data or 'password' not in data or 'type' not in data:
        return bad_request('Os campos username, fullname, password e type são obrigatórios')

    try:
        if data['type'] in EnumType.__members__:
            user_type = EnumType[data['type']].__str__()
        else:
            user_type = EnumType.anonymous.__str__()
    except (Exception, KeyError, LookupError) as e:
        return bad_request('Tipo de usuário inválido, {}'.format(e))

    new_user = User(
        username=data['username'],
        fullname=data['fullname'],
        password=User.generate_hash(data['password']),
        type=user_type
    )
    try:
        new_user.save_to_db()
        access_token = create_access_token(identity=data['username'], expires_delta=False)
        msg = 'Usuário {} criado com sucesso'.format(data['username'])
        current_app.logger.info(msg)
        db.session.commit()
        return jsonify({
            'message': msg,
            'access_token': access_token,
            'login': 'api/login'
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Error {}'.format(e))
        return jsonify({'message': 'Algo de errado não está certo'}), 500


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}

    if 'username' not in data or 'password' not in data:
        return bad_request('Os campos username e password são obrigatórios')

    current_user = User.find_by_username(data['username'])
    if not current_user:
        return bad_request('Usuário {} inexistente'.format(data['username']))

    if User.verify_hash(data['password'], current_user.password):
        access_token = create_access_token(identity=data['username'], expires_delta=False)
        return jsonify({
            'message': 'Logado como {}'.format(current_user.username),
            'access_token': access_token,
            'info': 'api/user'
        }), 200
    else:
        return {'message': 'Senha ou usuário incorretos'}, 400


@bp.route('/logout', methods=['POST'])
@jwt_required
def logout():
    jti = get_raw_jwt()['jti']
    try:
        revoked_token = RevokedToken(jti=jti)
        revoked_token.add()
        db.session.commit()
        msg = 'O seu token de acesso foi revogado com sucesso'
        current_app.logger.info(msg)

        return {'message': msg}, 200
    except Exception as e:
        msg = 'Algo de errado não está certo, {}'.format(e)
        current_app.logger.error(msg)
        db.session.rollback()
        return {'message': msg}, 500

# @bp.route('/task', methods=['GET'])
# @jwt_required
# def test():
#     username = get_jwt_identity()
#     current_user = User.find_by_username(username)
#     task = current_user.launch_task('test_task', 'TEST Evaluation', current_user.id)
#     return jsonify({
#                'message': 'JOB criada com sucesso',
#                'data': {
#                    'task': task.id,
#                    'url': 'api/task/' + str(task.id),
#                }
#            }), 201


@bp.route('/password/change', methods=['POST'])
@jwt_required
def change_pass():
    username = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    current_user = User.find_by_username(username)

    if 'current_password' not in data or 'new_password' not in data:
        return bad_request('Os campos current_password e new_password são obrigatórios')
    if not current_user:
        return bad_request('Usuário {} inexistente'.format(data['username']))

    if User.verify_hash(data['current_password'], current_user.password):
        try:
            User.change_password(username, data['new_password'])
            msg = 'Senha alterada com sucesso'
            current_app.logger.info(msg)
            try:
                jti = get_raw_jwt()['jti']
                revoked_token = RevokedToken(jti=jti)
                revoked_token.add()
                db.session.commit()
                return {
                           'message': 'Senha alterada com sucesso',
                       }, 200
            except Exception as e:
                db.session.rollback()
                return {'message': 'Algo de errado não está certo, {}'.format(e)}, 500
        except Exception as e:
            db.session.rollback()
            current_app.logger.error('Error {}'.format(e))
            return {'message': 'Algo de errado não está certo'}, 500
    return {'message': 'A senha atual não está correta'}, 422


@bp.route('/user', methods=['PUT', 'GET'])
@jwt_required
def user():
    data = request.get_json(silent=True) or {}
    username = get_jwt_identity()

    if request.method == 'PUT':

        if 'username' not in data or 'fullname' not in data or 'password' not in data or 'type' not in data:
            return bad_request('Os campos username, fullname, password e type são obrigatórios')

        current_user = User.find_by_username(username)
        new_user = User.find_by_username(data['username'])

        if not current_user:
            return bad_request('Usuário {} inexistente'.format(data['username']))

        if new_user:
            if (new_user.username != current_user.username) and (new_user.id != current_user.id):
                return bad_request('Usuário {} já esta em uso'.format(data['username']))

        try:
            current_user.update_to_db(data['username'], data['fullname'], data['type'])
            current_app.logger.info('Usuário alterada com sucesso')
            try:
                if data['username'].strip() != username.strip():
                    jti = get_raw_jwt()['jti']
                    revoked_token = RevokedToken(jti=jti)
                    revoked_token.add()
                db.session.commit()
                return {
                           'message': 'Usuário alterada com sucesso',
                       }, 200
            except Exception as e:
                db.session.rollback()
                return {'message': 'Algo de errado não está certo, {}'.format(e)}, 500
        except Exception as e:
            db.session.rollback()
            return {'message': 'Algo de errado não está certo, {}'.format(e)}, 500

    elif request.method == 'GET':
        user = User.find_by_username(username)
        user_schema = UserSchema()
        return user_schema.jsonify(user)
    else:
        return bad_request('Método não permitido')
