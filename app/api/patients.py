from flask import request, jsonify
from flask_restful import marshal, fields, reqparse, inputs

from app.models import User, EnumType, RevokedToken, Patient
from flask_jwt_extended import (create_access_token, jwt_required, get_raw_jwt, get_jwt_identity)
from app.api import bp
from flask import current_app
from app.api.errors import bad_request
from app import db


@bp.route('/patient/registration', methods=['POST'])
@jwt_required
def registration():
    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument('name', help='Nome completo é obrigatório', required=True)
    parser.add_argument(
        'birth',
        help='Data de nascimento é obrigatória e deve estar no formato YYYY-mm-dd',
        required=True,
        type=inputs.date
    )
    parser.add_argument(
        'sex',
        choices=('M', 'F', ''),
        help='Sexualidade deve ser um valor válido (M, F), ou não deve ser fornecida',
        nullable=True,
        required=False
    )
    parser.add_argument('school', help='Escola é obrigatória', required=True)
    parser.add_argument(
        'school_type',
        choices=('PUB', 'PRI'),
        help='Orgão escolar é obrigatório e deve ser uma string válida (PUB, PRI) ',
        required=True
    )
    parser.add_argument('caregiver', nullable=True)
    parser.add_argument('phone', nullable=True)
    parser.add_argument('city', help="A Cidade é obrigatória", required=True)
    parser.add_argument('state', help="O Estado é obrigatória", required=True)
    parser.add_argument('address', nullable=True)

    data = parser.parse_args()

    if Patient.find_by_name(data['name']):
        current_app.logger.warn('Paciente {} já existe'.format(data['name']))
        return {'message': 'Paciente {} já existe'.format(data['name'])}, 422

    new_patient = Patient(
        name=data['name'],
        birth=data['birth'],
        sex=data['sex'],
        school=data['school'],
        school_type=data['school_type'],
        caregiver=data['caregiver'],
        phone=data['phone'],
        city=data['city'],
        state=data['state'],
        address=data['address'],
    )

    try:
        new_patient.save_to_db()
        current_app.logger.info('Paciente {} criado com sucesso'.format(data['name']))
        return {
                   'message': 'Paciente {} criado com sucesso'.format(data['name']),
                   'info': 'api/pacient/{}'.format(new_patient.id)
               }, 201
    except Exception as e:
        current_app.logger.error('Error - PACIENT -> {}'.format(e))
        return {'message': 'Algo de errado não está certo, não foi possível criar o paciente'}, 500