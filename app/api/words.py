from flask import request, jsonify, g
from app.api.auth import token_auth, only_therapist
from app.api.errors import bad_request
from app.models import Word, WordSchema, WordTranscriptionSchema, WordTranscription
from app.api import bp
from flask import current_app


@bp.route('/word', methods=['POST'])
@token_auth.login_required
@only_therapist
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


@bp.route('/word/<string:word>', methods=['GET'])
@token_auth.login_required
def word_info(word=None):
    if not word:
        return bad_request('Palavra não informada')

    word_data = Word.find_by_word(word)

    if not word_data:
        return bad_request('Palavra não encontrada')

    word_schema = WordSchema()
    transcriptions_schema = WordTranscriptionSchema(many=True)

    transcriptions = WordTranscription.find_by_word_id(word_id=word_data.id)

    word_output = word_schema.dump(word_data).data
    transcriptions_output = transcriptions_schema.dump(transcriptions).data
    return jsonify({
        'data': word_output,
        'transcriptions': transcriptions_output
    }), 200


@bp.route('/word/<string:word>', methods=['PUT', 'DELETE'])
@token_auth.login_required
@only_therapist
def word_change(word=None):
    if not word:
        return bad_request('Palavra não informada')

    word_data = Word.find_by_word(word)

    if not word_data:
        return bad_request('Palavra não encontrada')

    if request.method == 'PUT':

        data = request.get_json(silent=True) or {}

        if 'word' not in data:
            return bad_request('O campo word é obrigatório')

        new_word = Word.find_by_word(data['word'])

        if new_word:
            if (new_word.word != word_data.word) and (new_word.id != word_data.id):
                current_app.logger.warn('Palavra {} já existe'.format(data['word']))
                return jsonify({'message': 'Palavra {} já existe'.format(data['word'])}), 400

        try:
            word_data.update_to_db(word=data['word'], tip=data['tip'] if 'tip' in data else None)

            current_app.logger.info('Palavra {} atualizada com sucesso'.format(data['word']))
            return jsonify({
                'message': 'Palavra {} atualizada com sucesso'.format(data['word']),
                'route': '/api/word/{}'.format(word_data.word)
            }), 200
        except Exception as e:
            current_app.logger.error('Error {}'.format(e))
            return jsonify({'message': 'Algo de errado não está certo, não foi possível atualizar sua palavra'}), 500

    elif request.method == 'DELETE':

        try:
            Word.delete_by_word(word)
            current_app.logger.info('Palavra {} deletada com sucesso'.format(word))
            return jsonify({
                'message': 'Palavra {} deletada com sucesso'.format(word),
            }), 202
        except Exception as e:
            current_app.logger.error('Error {}'.format(e))
            return jsonify({'message': 'Algo de errado não está certo, não foi possível deletar sua palavra'}), 500


@bp.route('/word/all', methods=['GET'])
@token_auth.login_required
def word_all():
    word_schema = WordSchema(many=True)
    word_data = Word.return_all()
    word_output = word_schema.dump(word_data).data
    return jsonify({
        'data': word_output
    }), 200