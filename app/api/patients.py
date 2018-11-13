from flask import request, jsonify, g
from app import db
from app.api.auth import token_auth, only_therapist, only_anonymous
from app.api.errors import bad_request
from app.helpers import validate_date, is_in_choices
from app.models import Patient, PatientSchema, EnumType, User
from app.api import bp
from flask import current_app


@bp.route('/patient/registration', methods=['POST'])
@token_auth.login_required
@only_therapist
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

    try:
        name_list = data['name'].split()  # separa o nome em espaços
        username = name_list[0].lower() + '-' + name_list[-1].lower()  # gera o nome de usário com base no nome completo
        user_type = EnumType.anonymous.__str__()  # coloca como tipo anonymous
        if User.find_by_username(username):  # username já em uso
            same_username = User.count_by_username(username)
            username = str(username + '-' + same_username)  # redefine o nome de usuário

        new_user = User(  # cria novo usuário
            username=username,
            fullname=data['name'],
            password=User.generate_hash('primeiroacesso'),
            # TODO: pensar em algo melhor na criação do primeiro acesso, como por exemplo, madar um e-mail com as informações de login
            type=user_type
        )
        new_user.save_to_db()
        current_app.logger.info('Usuário {} criado com sucesso'.format(username))

    except (Exception, KeyError, LookupError) as e:
        db.session.rollback()
        current_app.logger.error('Error {}'.format(e))
        return jsonify({'message': 'Algo de errado não está certo'}), 500

    new_patient = Patient(
        name=data['name'],
        user_id=new_user.id,
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
            'info': 'api/pacient/{}'.format(new_patient.id),
            'id': new_patient.id
        }), 201
    except Exception as e:
        current_app.logger.error('Error - PACIENT -> {}'.format(e))
        return jsonify({'message': 'Algo de errado não está certo, não foi possível criar o paciente'}), 500


@bp.route('/patient/<int:patient_id>', methods=['GET', 'PUT', 'DELETE'])
@token_auth.login_required
@only_therapist
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

    elif request.method == 'DELETE':
        try:
            patient.delete()
            return jsonify({
                'message': 'Paciente deletado com sucesso',
            }), 202
        except Exception as e:
            current_app.logger.error('DELETE PACIENT -> {}'.format(e))
            return jsonify({'message': 'Paciente não foi deletado, {}'.format(e)}), 500

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


@bp.route('/patient/info', methods=['GET', 'PUT'])
@token_auth.login_required
@only_anonymous
def anonymous_patient_info_change():
    patient = Patient.get_patient_by_user_id(g.current_user.id)

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


@bp.route('/patient', methods=['GET'])
@token_auth.login_required
@only_therapist
def patient_by_name():
    patient = request.args.get('name')

    if not patient:
        return bad_request('Paciente não informado')

    patients = Patient.ilike_by_name(patient)
    patient_schema = PatientSchema()
    output = patient_schema.dump(patients, many=True).data
    return jsonify(output), 200


@bp.route('/patient/all', methods=['GET'])
@token_auth.login_required
@only_therapist
def patient_get_all():
    patients = Patient.return_all()
    patient_schema = PatientSchema()
    output = patient_schema.dump(patients, many=True).data
    return jsonify(output), 200
