import json
import os

from flask import request, jsonify, g

from sklearn.datasets import load_svmlight_file
from sklearn.neighbors import KNeighborsClassifier
from sqlalchemy import exists
from werkzeug.utils import secure_filename

from app import db
from app.helpers import allowed_file, generate_hash_from_filename

from app.api.auth import token_auth
from app.api.errors import bad_request
from app.api import bp
from flask import current_app

from app.helpers import is_in_choices
from app.models import Patient, Evaluation, EvaluationSchema, WordEvaluation, WordEvaluationSchema, EnumType, Word, \
    WordTranscription

init_training = 0
clf = {}


@bp.route('/evaluation', methods=['POST'])
@token_auth.login_required
def evaluation_registration():
    data = request.get_json(silent=True) or {}

    if 'type' in data:
        if not is_in_choices(data['type'], ['R', 'N', 'F']):
            return bad_request('O tipo de avaliação deve ser uma string válida (R,N,F)')

    patient = None
    current_user = g.current_user

    if 'patient_id' in data and current_user.type == EnumType.therapist.__str__():  # terapeuta pode submeter avaliações para qualquer tipo de paciente
        patient = Patient.find_by_id(data['patient_id'])
    elif current_user.type == EnumType.anonymous.__str__():  # usuário anonymous somente submete avaliação a ele mesmo
        patient = Patient.get_patient_by_user_id(current_user.id)

    if not patient:
        current_app.logger.warn('Paciente inexistente')
        return bad_request('Paciente inexistente')

    new_evaluation = Evaluation(
        type=data['type'] if 'type' in data else None,
        patient_id=patient.id,
        evaluator_id=current_user.id,
    )

    try:
        new_evaluation.save_to_db()
        current_app.logger.info('Avaliação criada com sucesso')
        return jsonify({
            'message': 'Avaliação criada com sucesso',
            'route': '/api/evaluation/{}'.format(new_evaluation.id),
            'id': new_evaluation.id
        }), 201
    except Exception as e:
        current_app.logger.error('Error {}'.format(e))
        return jsonify({
            'message': 'Algo de errado não está certo, não foi possível cadastrar sua Avaliação',
            'error': '{}'.format(e)
        }), 500


@bp.route('/evaluation/<int:evaluation_id>', methods=['GET', 'PUT'])
@token_auth.login_required
def evaluation_info_change(evaluation_id=None):
    if not evaluation_id:
        return bad_request('Avaliação não informada')

    evaluation = Evaluation.find_by_id(evaluation_id)

    if not evaluation:
        return jsonify({'message': 'Avaliação não encontrada'}), 404

    if g.current_user.type == EnumType.anonymous.__str__() and evaluation.evaluator_id != g.current_user.id:  # usuários anonymous somente podem requisitar suas próprias avaliações
        return jsonify({'message': 'Avaliação não encontrada'}), 404

    if request.method == 'GET':
        evaluation_schema = EvaluationSchema()
        evaluation_output = evaluation_schema.dump(evaluation).data
        word_evaluations = WordEvaluation.find_evaluations_by_id(evaluation_id)
        word_evaluation_schema = WordEvaluationSchema(many=True)
        word_evaluation_output = word_evaluation_schema.dump(word_evaluations).data

        result = {'data': evaluation_output}
        result['data']['evaluations'] = word_evaluation_output

        return jsonify(result), 200

    if request.method == 'PUT':
        data = request.get_json(silent=True) or {}

        if 'type' in data and not is_in_choices(data['type'], ['R', 'N', 'F']):
            return bad_request('O tipo de avaliação deve ser uma string válida (R,N,F)')
        patient = None
        if 'patient_id' in data and g.current_user.type == EnumType.therapist.__str__():  # terapeuta pode submeter avaliações para qualquer tipo de paciente
            patient = Patient.find_by_id(data['patient_id'])
        elif g.current_user.type == EnumType.anonymous.__str__():  # usuário anonymous somente submete avaliação a ele mesmo
            patient = Patient.get_patient_by_user_id(g.current_user.id)

        if not patient:
            current_app.logger.warn('Paciente inexistente')
            return bad_request('Paciente inexistente')

        try:
            evaluation.update_to_db(
                type=data['type'] if 'type' in data else None,
                patient_id=patient.id
            )
            current_app.logger.info('Avaliação alterada com sucesso')
            return jsonify({
                'message': 'Avaliação alterada com sucesso',
                'id': evaluation.id,
                'info': 'api/evaluation/{}'.format(evaluation.id)
            }), 200
        except Exception as e:
            current_app.logger.error('PUT EVALUATION -> {}'.format(e))
            return jsonify({'message': 'Algo de errado não está certo, {}'.format(e)}), 500


@bp.route('/word/<string:word>/evaluation/<int:evaluation_id>', methods=['GET', 'POST'])
@token_auth.login_required
def word_evaluation(word=None, evaluation_id=None):
    global init_training,clf
    if not word:
        return bad_request('Palavra não informada')

    if not evaluation_id:
        return bad_request('Avaliação não informada')

    evaluation = Evaluation.find_by_id(evaluation_id) if g.current_user.type == EnumType.therapist.__str__() \
        else Evaluation.find_user_evaluation_by_id(evaluation_id, g.current_user.id)

    if not evaluation:
        return jsonify({'message': 'Avaliação não encontrada'}), 404

    # if evaluation.evaluator_id != g.current_user.id:
    #     return jsonify({'message': 'Avaliação não encontrada'}), 404

    word_data = Word.find_by_word(word)

    if not word_data:
        return bad_request('Palavra não encontrada')

    current_user = g.current_user
    therapist_user = current_user.type == EnumType.therapist.__str__()

    if request.method == 'POST':

        if 'file' not in request.files:
            return bad_request('Arquivo de audio não fornecido')

        audio = request.files['file']

        if audio.filename == '':
            return bad_request('Arquivo de audio não selecionado')

        data = json.loads(request.form['form']) if 'form' in request.form else (request.form or {})

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

                #    Aceita 2 tipos de avaliação do terapeuta
                #    1 - Indicando a transcrição identificada (transcription_eval) e a transcrição alvo (transcription_target_id)
                #    2 - Indicando se a pronúncia foi dita corretamente diretamente (therapist_eval)

                target_transc = WordTranscription.find_by_transcription_id(
                    data['transcription_target_id']) if 'transcription_target_id' in data and therapist_user else None
                eval_transc = WordTranscription.find_by_transcription_id(
                    data['transcription_eval_id']) if 'transcription_eval_id' in data and therapist_user else None

                if not target_transc and 'transcription_target_id' in data and therapist_user:
                    return bad_request('Transcrição alvo não encontrada')
                if not eval_transc and 'transcription_eval_id' in data and therapist_user:
                    return bad_request('Transcrição avaliada não encontrada')

                new_word_eval = WordEvaluation(
                    evaluation_id=evaluation.id,
                    word_id=word_data.id,
                    transcription_target_id=target_transc.id if target_transc is not None else target_transc,
                    transcription_eval_id=eval_transc.id if eval_transc is not None else eval_transc,
                    repetition=data['repetition'] if 'repetition' in data else False,
                    audio_path=full_path,
                    therapist_eval=int(data['therapist_eval']) if 'therapist_eval' in data and therapist_user else None
                )

                try:

                    row_exists = db.session.query(
                        db.exists().where(WordEvaluation.evaluation_id == evaluation_id).where(
                            WordEvaluation.word_id == word_data.id)).scalar()

                    if row_exists:
                        raise Exception('Uma avaliação com estes dados já foi submetida')

                    new_word_eval.save_to_db()

                    #  GOOGLE API AUDIO EVALUATION
                    # task1 = current_user.launch_task(
                    #     'google_transcribe_audio',
                    #     'Audio Evaluation with Google API',
                    #     evaluation.id,
                    #     word_data.id,
                    #     word,
                    #     full_path
                    # )

                    if init_training == 0:

                        for key in ['Anel', 'Barriga', 'Batom', 'Bebe', 'Beijo', 'Biblioteca', 'Bicicleta', 'Bolsa']:
                            X_train, y_train = load_svmlight_file('./app/training_files/' + key)

                            # clf[key] = tree.DecisionTreeClassifier()
                            clf[key] = KNeighborsClassifier()

                            current_app.logger.info("ML API -> Fitting classifier...")
                            clf[key].fit(X_train, y_train)
                        init_training = 1

                    # ML AUDIO EVALUATION
                    task2 = current_user.launch_task(
                        name='ml_transcribe_audio',
                        description='Audio Evaluation',
                        evaluation_id=evaluation.id,
                        word_id=word_data.id,
                        word=word,
                        wd_audio_path=full_path,
                        clf=clf
                    )

                    db.session.commit()
                    return jsonify({
                        'message': 'Avaliação do audio criada com sucesso e está sendo processada...',
                        'data': {
                            # 'task_api_id': task1.id,
                            # 'url_api': 'api/task/' + str(task1.id),
                            'task_ml_id': task2.id,
                            'url_ml': 'api/task/' + str(task2.id),
                        }
                    }), 201
                except Exception as e:
                    db.session.rollback()
                    if os.path.exists(full_path):
                        os.remove(full_path)
                    current_app.logger.error('POST WORD_EVALUATION -> {}'.format(e))
                    return jsonify({'message': 'Algo de errado não está certo, {}'.format(e)}), 500
        else:
            return jsonify({'message': 'Arquivo de audio não permitido'}), 422

    if request.method == 'GET':

        evaluation = Evaluation.find_by_id(evaluation_id) if therapist_user \
            else Evaluation.find_user_evaluation_by_id(evaluation_id, current_user.id)

        word_eval = WordEvaluation.find_word_evaluation_by_id_and_word(evaluation.id, word)

        if not word_eval:
            return bad_request('avaliação não encontrada')

        word_eval_schema = WordEvaluationSchema()
        eval_output = word_eval_schema.dump(word_eval).data
        return jsonify(eval_output)