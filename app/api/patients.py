from flask import request, jsonify
from app import db
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.helpers import validate_date, is_in_choices
from app.models import Patient, PatientSchema
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


@bp.route('/patient/<int:patient_id>', methods=['GET', 'PUT'])
@token_auth.login_required
def patient_info_change(patient_id=None):
    if not patient_id:
        return bad_request('Paciente não informado')

    patient = Patient.find_by_id(patient_id)

    if not patient:
        return bad_request('Paciente não encontrado')

    if request.method == 'GET':

        patient_schema = PatientSchema()
        output = patient_schema.dump(patient).data
        return jsonify(output), 200

    elif request.method == 'PUT':

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

        try:
            patient.update_to_db(
                data['name'],
                data['birth'],
                data['sex'],
                data['school'],
                data['school_type'],
                data['caregiver'] if 'caregiver' in data else None,
                data['phone'] if 'phone' in data else None,
                data['city'],
                data['state'],
                data['address'] if 'address' in data else None
            )
            current_app.logger.info('Paciente alterado com sucesso')
            db.session.commit()
            return jsonify({
                'message': 'Paciente {} alterado com sucesso'.format(data['name']),
                'info': 'api/pacient/{}'.format(patient.id)
            }), 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error('PUT PACIENT -> {}'.format(e))
            return jsonify({'message': 'Algo de errado não está certo, {}'.format(e)}), 500

    else:
        return bad_request({'msg': 'Método não permitido'})


@bp.route('/patient/all', methods=['GET'])
@token_auth.login_required
def patient_get_all():
    patients = Patient.return_all()
    patient_schema = PatientSchema()
    output = patient_schema.dump(patients, many=True).data
    return jsonify(output), 200
