import os
from flask import request, jsonify, g
from werkzeug.utils import secure_filename

from app import db
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.helpers import allowed_file, generate_hash_from_filename
from app.models import Word, WordSchema, WordTranscriptionSchema, WordTranscription, Evaluation, WordEvaluation, \
    WordEvaluationSchema
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
        return bad_request('Palavra não informada')

    word_data = Word.find_by_word(word)

    if not word_data:
        return bad_request('Palavra não encontrada')

    if request.method == 'GET':

        word_schema = WordSchema()
        transcriptions_schema = WordTranscriptionSchema(many=True)

        transcriptions = WordTranscription.find_by_word_id(word_id=word_data.id)

        word_output = word_schema.dump(word_data).data
        transcriptions_output = transcriptions_schema.dump(transcriptions).data
        return jsonify({
            'data': word_output,
            'transcriptions': transcriptions_output
        }), 200

    elif request.method == 'PUT':

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
            }), 201
        except Exception as e:
            current_app.logger.error('Error {}'.format(e))
            return jsonify({'message': 'Algo de errado não está certo, não foi possível atualizar sua palavra'}), 500

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


@bp.route('/word/<string:word>/evaluation/<int:evaluation_id>', methods=['GET', 'POST'])
@token_auth.login_required
def word_evaluation(word=None, evaluation_id=None):
    if not word:
        return bad_request('Palavra não informada')

    if not evaluation_id:
        return bad_request('Avaliação não informada')

    evaluation = Evaluation.find_by_id(evaluation_id)

    if not evaluation:
        return jsonify({'message': 'Avaliação não encontrada'}), 404

    if evaluation.evaluator_id != g.current_user.id:
        return jsonify({'message': 'Avaliação não encontrada'}), 404

    word_data = Word.find_by_word(word)

    if not word_data:
        return bad_request('Palavra não encontrada')

    if request.method == 'POST':

        if 'file' not in request.files:
            return bad_request('Arquivo de audio não fornecido')

        audio = request.files['file']

        if audio.filename == '':
            return bad_request('Arquivo de audio não selecionado')

        data = request.form or {}

        if 'transcription_target_id' not in data or 'transcription_eval' not in data:
            return bad_request('Os campos transcription_target_id e transcription_eval são obrigatórios')

        target_transc = WordTranscription.find_by_transcription_id(data['transcription_target_id'])

        if not target_transc:
            return bad_request('Transcrição alvo não encontrada')

        if audio and allowed_file(audio.filename):
            filename = secure_filename(audio.filename)

            full_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'],
                str(generate_hash_from_filename(filename) + '.' + filename.rsplit('.', 1)[1].lower())
            )

            try:
                audio.save(full_path)
            except Exception as e:
                current_app.logger.error('POST WORD_EVALUATION  SAVE AUDIO -> {}'.format(e))
                return jsonify({'message': 'Algo de errado não está certo, {}'.format(e)}), 500
            else:

                therapist_eval = None
                if 'transcription_eval' in data:
                    therapist_eval = data['transcription_eval'] == target_transc.transcription

                new_word_eval = WordEvaluation(
                    evaluation_id=evaluation.id,
                    word_id=word_data.id,
                    transcription_target_id=target_transc.id,
                    transcription_eval=data['transcription_eval'] if 'transcription_eval' in data else None,
                    repetition=data['repetition'] if 'repetition' in data else False,
                    audio_path=full_path,
                    therapist_eval=therapist_eval
                )

                try:

                    current_user = g.current_user

                    new_word_eval.save_to_db()
                    db.session.commit()

                    #  GOOGLE API AUDIO EVALUATION
                    task1 = current_user.launch_task(
                        'google_transcribe_audio',
                        'Audio Evaluation with Google API',
                        evaluation.id,
                        word_data.id,
                        word,
                        full_path
                    )

                    # ML AUDIO EVALUATION
                    task2 = current_user.launch_task(
                        'ml_transcribe_audio',
                        'Audio Evaluation',
                        evaluation.id,
                        word_data.id,
                        word,
                        full_path
                    )
                    return jsonify({
                        'message': 'Avaliação do audio criada com sucesso e está sendo processada...',
                        'data': {
                            'task_api_id': task1.id,
                            'url_api': 'api/task/' + str(task1.id),
                            'task_ml_id': task2.id,
                            'url_ml': 'api/task/' + str(task2.id),
                        }
                    }), 201
                except Exception as e:
                    db.session.rollback()
                    audio.delete(full_path)
                    current_app.logger.error('POST WORD_EVALUATION -> {}'.format(e))
                    return jsonify({'message': 'Algo de errado não está certo, {}'.format(e)}), 500
        else:
            return jsonify({'message': 'Arquivo de audio não permitido'}), 422

    if request.method == 'GET':

        word_eval = WordEvaluation.find_word_evaluation_by_id_and_word(evaluation_id, word)

        if not word_eval:
            return bad_request('avaliação não encontrada')

        word_eval_schema = WordEvaluationSchema()
        eval_output = word_eval_schema.dump(word_eval).data
        return jsonify(eval_output)
