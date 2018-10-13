from flask import request, jsonify
from flask_restful import marshal, fields, reqparse, inputs
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.helpers import validate_date, is_in_choices
from app.models import Patient
from app.api import bp
from flask import current_app


@bp.route('/patient/registration', methods=['POST'])
@token_auth.login_required
def patient_registration():
    data = request.get_json(silent=True) or {}

    if 'name' not in data or 'birth' not in data or 'school_type' not in data \
            or 'school' not in data or 'city' not in data or 'state' not in data or 'sex' not in data:
        return bad_request('Os campos name, birth, sex, school_type, school, city e state são obrigatórios')

    if not validate_date(data['birth']):
        return bad_request('O campo birth deve estar no formato YYY-MM-DD')

    if not is_in_choices(data['sex'], ['M', 'F', '']):
        return bad_request('Sexualidade deve ser um valor válido (M, F), ou não deve ser fornecida')

    if not is_in_choices(data['school_type'], ['PUB', 'PRI']):
        return bad_request('Orgão escolar é obrigatório e deve ser uma string válida (PUB, PRI) ')

    if Patient.find_by_name(data['name']):
        current_app.logger.warn('Paciente {} já existe'.format(data['name']))
        return jsonify({'message': 'Paciente {} já existe'.format(data['name'])}), 422

    new_patient = Patient(
        name=data['name'],
        birth=data['birth'],
        sex=data['sex'],
        school=data['school'],
        school_type=data['school_type'],
        caregiver=data['caregiver'] if 'caregiver' in data else None,
        phone=data['phone'] if 'phone' in data else None,
        city=data['city'],
        state=data['state'],
        address=data['address'] if 'address' in data else None,
    )

    try:
        new_patient.save_to_db()
        current_app.logger.info('Paciente {} criado com sucesso'.format(data['name']))
        return jsonify({
            'message': 'Paciente {} criado com sucesso'.format(data['name']),
            'info': 'api/pacient/{}'.format(new_patient.id)
        }), 201
    except Exception as e:
        current_app.logger.error('Error - PACIENT -> {}'.format(e))
        return jsonify({'message': 'Algo de errado não está certo, não foi possível criar o paciente'}), 500


@bp.route('/patient/<int:patient_id>', methods=['POST'])
@token_auth.login_required
def get(patient_id=None):
    if not patient_id:
        return {'message': 'Paciente não encontrado'}, 404

    patient = Patient.find_by_id(patient_id)

    if not patient:
        return {'message': 'Paciente não encontrado'}, 404

    resource_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'birth': fields.String,
        'sex': fields.String,
        'school': fields.String,
        'school_type': fields.String,
        'caregiver': fields.String,
        'phone': fields.String,
        'city': fields.String,
        'state': fields.String,
        'address': fields.String,
    }
    return marshal(patient, resource_fields, envelope='data')
