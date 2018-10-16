from flask import request, jsonify
from app import db
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.helpers import validate_date, is_in_choices
from app.models import WordTranscriptionSchema, WordTranscription, Word
from app.api import bp
from flask import current_app


@bp.route('/word/transcription', methods=['POST'])
@token_auth.login_required
def word_transcription_registration():
    data = request.get_json(silent=True) or {}

    if 'word' not in data or 'transcription' not in data:
        return bad_request('O campo word e transcription são obrigatórios')

    word = Word.find_by_word(data['word'])

    if word is None:
        current_app.logger.warn('Palavra {} inexistente'.format(data['word']))
        return jsonify({'message': 'Palavra {} inexistente'.format(data['word'])}), 400

    new_transcription = WordTranscription(
        word_id=word.id,
        transcription=str(data['transcription']).strip()
    )
    try:
        new_transcription.save_to_db()

        current_app.logger.info('Transcrição de {} criada com sucesso'.format(data['word']))
        return jsonify({
            'message': 'Transcrição de {} criada com sucesso'.format(data['word']),
            'route': '/api/transcription/{}'.format(new_transcription.id)
        }), 201
    except Exception as e:
        current_app.logger.error('Error {}'.format(e))
        return jsonify({'message': 'Algo de errado não está certo, não foi possível cadastrar sua Transcrição'}), 500


@bp.route('/word/transcription/<int:transcription_id>', methods=['GET', 'PUT', 'DELETE'])
@token_auth.login_required
def word_transcription_info_change(transcription_id=None):
    if not transcription_id:
        return bad_request('Transcrição não informada')

    transc = WordTranscription.find_by_transcription_id(transcription_id)

    if not transc:
        return bad_request('Transcrição não encontrada')

    if request.method == 'GET':

        transcriptions_schema = WordTranscriptionSchema(many=True)
        transcriptions_output = transcriptions_schema.dump(transc).data
        return jsonify(transcriptions_output), 200

    elif request.method == 'PUT':

        data = request.get_json(silent=True) or {}

        if 'word' not in data or 'transcription' not in data:
            return bad_request('O campo word e transcription é obrigatório')

        word = Word.find_by_word(data['word'])

        if word is None:
            current_app.logger.warn('Palavra {} inexistente'.format(data['word']))
            return jsonify({'message': 'Palavra {} inexistente'.format(data['word'])}), 400

        try:
            transc.update_to_db(
                word=data['word'],
                transcription=data['transcription'],
                type=data['type'] if 'type' in data else None
            )

            current_app.logger.info('transcrição {} atualizada com sucesso'.format(data['transcription']))
            return jsonify({
                       'message': 'transcrição {} atualizada com sucesso'.format(data['transcription']),
                       'route': '/api/word/transcription/{}'.format(transc.id)
                   }), 200
        except Exception as e:
            current_app.logger.error('Error {}'.format(e))
            return jsonify({'message': 'Algo de errado não está certo, não foi possível atualizar sua transcrição'}), 500

    elif request.method == 'DELETE':

        try:
            transc.delete_transcription()
            current_app.logger.info('Transcrição {} deletada com sucesso'.format(transc.transcription))
            return jsonify({
                'message': 'Transcrição {} deletada com sucesso'.format(transc.transcription),
            }), 200
        except Exception as e:
            current_app.logger.error('Error {}'.format(e))
            return jsonify({'message': 'Algo de errado não está certo, não foi possível deletar sua Transcrição'}), 500
