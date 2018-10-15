from flask import request, jsonify
from app import db
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.helpers import validate_date, is_in_choices
from app.models import Word, WordSchema
from app.api import bp
from flask import current_app


@bp.route('/word', methods=['POST'])
@token_auth.login_required
def word_registration():
    data = request.get_json(silent=True) or {}

    if 'word' not in data:
        return bad_request('O campo word é obrigatório')

    if Word.find_by_word(data['word']):
        current_app.logger.warn('Palavra {} já existe'.format(data['word']))
        return jsonify({'message': 'Palavra {} já existe'.format(data['word'])})

    new_word = Word(
        word=data['word'],
        tip=data['tip'] if 'tip' in data else None
    )
    try:
        new_word.save_to_db()
        current_app.logger.info('Palavra {} criada com sucesso'.format(data['word']))
        return jsonify({
            'message': 'Palavra {} criada com sucesso'.format(data['word']),
            'route': '/api/word/{}'.format(new_word.word)
        }), 201
    except Exception as e:
        current_app.logger.error('Error {}'.format(e))
        return jsonify({'message': 'Algo de errado não está certo, não foi possível cadastrar sua palavra'}), 500


@bp.route('/word/<string:word>', methods=['GET', 'PUT', 'DELETE'])
@token_auth.login_required
def word_info_change(word=None):
    if not word:
        return bad_request('Palavra não informado')

    word = Word.find_by_word(word)

    if not word:
        return bad_request('Palavra não encontrado')

    if request.method == 'GET':

        word_schema = WordSchema()
        output = word_schema.dump(word).data
        return jsonify(output), 200

    elif request.method == 'PUT': # TODO
        return 'PUT'

    elif request.method == 'DELETE':
        try:
            Word.delete_by_word(word)
            current_app.logger.info('Palavra {} deletada com sucesso'.format(word))
            return jsonify({
                'message': 'Palavra {} deletada com sucesso'.format(word),
            })
        except Exception as e:
            current_app.logger.error('Error {}'.format(e))
            return jsonify({'message': 'Algo de errado não está certo, não foi possível deletar sua palavra'}), 500