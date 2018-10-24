from flask import request, jsonify, g
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.api import bp
from flask import current_app

from app.helpers import is_in_choices
from app.models import Patient, Evaluation, EvaluationSchema, WordEvaluation, WordEvaluationSchema


@bp.route('/evaluation', methods=['POST'])
@token_auth.login_required
def evaluation_registration():
    data = request.get_json(silent=True) or {}

    if 'patient_id' not in data or 'type' not in data:
        return bad_request('O campo patient_id e type são obrigatórios')

    if not is_in_choices(data['type'], ['R', 'N', 'F']):
        return bad_request('O tipo de avaliação deve ser uma string válida (R,N,F)')

    patient = Patient.find_by_id(data['patient_id'])

    if not patient:
        current_app.logger.warn('Paciente inexistente')
        return bad_request('Paciente inexistente')

    current_user = g.current_user

    new_evaluation = Evaluation(
        type=data['type'],
        patient_id=patient.id,
        evaluator_id=current_user.id,
    )

    try:
        new_evaluation.save_to_db()
        current_app.logger.info('Avaliação criada com sucesso')
        return jsonify({
            'message': 'Avaliação criada com sucesso',
            'route': '/api/evaluation/{}'.format(new_evaluation.id)
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

    if evaluation.evaluator_id != g.current_user.id:
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
        if 'patient_id' not in data or 'type' not in data:
            return bad_request('O campo patient_id e type são obrigatórios')

        if not is_in_choices(data['type'], ['R', 'N', 'F']):
            return bad_request('O tipo de avaliação deve ser uma string válida (R,N,F)')

        patient = Patient.find_by_id(data['patient_id'])

        if not patient:
            current_app.logger.warn('Paciente inexistente')
            return bad_request('Paciente inexistente')

        try:
            evaluation.update_to_db(type=data['type'], patient_id=data['patient_id'])
            current_app.logger.info('Avaliação alterada com sucesso')
            return jsonify({
                'message': 'Avaliação alterada com sucesso',
                'info': 'api/evaluation/{}'.format(evaluation.id)
            }), 200
        except Exception as e:
            current_app.logger.error('PUT EVALUATION -> {}'.format(e))
            return jsonify({'message': 'Algo de errado não está certo, {}'.format(e)}), 500

