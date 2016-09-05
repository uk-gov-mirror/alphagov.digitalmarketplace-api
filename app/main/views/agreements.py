from datetime import datetime
from flask import jsonify, abort
from .. import main
from sqlalchemy.exc import IntegrityError
from dmapiclient.audit import AuditTypes
from ...models import (
    AuditEvent, db, FrameworkAgreement, User
)

from ...utils import (
    get_json_from_request,
    json_has_required_keys,
    json_has_keys,
    validate_and_return_updater_request,
)

from ...supplier_utils import validate_agreement_details_data


@main.route('/agreements/<int:agreement_id>', methods=['GET'])
def get_framework_agreement(agreement_id):
    framework_agreement = FrameworkAgreement.query.filter(FrameworkAgreement.id == agreement_id).first_or_404()

    return jsonify(agreement=framework_agreement.serialize())


@main.route('/agreements/<int:agreement_id>', methods=['POST'])
def update_framework_agreement(agreement_id):
    framework_agreement = FrameworkAgreement.query.filter(FrameworkAgreement.id == agreement_id).first_or_404()
    framework_agreement_details = framework_agreement.supplier_framework.framework.framework_agreement_details

    json_payload = get_json_from_request()
    updater_json = validate_and_return_updater_request()
    json_has_required_keys(json_payload, ["agreement"])
    update_json = json_payload["agreement"]

    json_has_keys(update_json, optional_keys=['signedAgreementDetails', 'signedAgreementPath'])

    # TODO Behaviour to be introduced after next step of refactoring
    # if (
    #     framework_agreement.signed_agreement_returned_at
    #     and ('signedAgreementDetails' in update_json or 'signedAgreementPath' in update_json)
    # ):
    #     abort(400, "Can not update signedAgreementDetails or signedAgreementPath if agreement has been signed")

    if update_json.get('signedAgreementDetails'):
        if not framework_agreement_details or not framework_agreement_details.get('frameworkAgreementVersion'):
            abort(
                400,
                "Can not update signedAgreementDetails for a framework agreement without a frameworkAgreementVersion"
            )

        framework_agreement.update_signed_agreement_details_from_json(update_json['signedAgreementDetails'])
        validate_agreement_details_data(
            framework_agreement.signed_agreement_details,
            enforce_required=False
        )

    if update_json.get('signedAgreementPath'):
        framework_agreement.signed_agreement_path = update_json['signedAgreementPath']

    audit_event = AuditEvent(
        audit_type=AuditTypes.update_agreement,
        user=updater_json['updated_by'],
        data={
            'supplierId': framework_agreement.supplier_id,
            'frameworkSlug': framework_agreement.supplier_framework.framework.slug,
            'update': update_json},
        db_object=framework_agreement
    )

    try:
        db.session.add(framework_agreement)
        db.session.add(audit_event)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify(message="Database Error: {0}".format(e)), 400

    return jsonify(agreement=framework_agreement.serialize())


@main.route('/agreements/<int:agreement_id>/sign', methods=['POST'])
def sign_framework_agreement(agreement_id):
    framework_agreement = FrameworkAgreement.query.filter(FrameworkAgreement.id == agreement_id).first_or_404()
    framework_agreement_details = framework_agreement.supplier_framework.framework.framework_agreement_details

    json_payload = get_json_from_request()
    updater_json = validate_and_return_updater_request()
    update_json = None

    if framework_agreement_details and framework_agreement_details.get('frameworkAgreementVersion'):
        json_has_required_keys(json_payload, ["agreement"])
        update_json = json_payload["agreement"]

        json_has_keys(update_json, required_keys=['signedAgreementDetails'])

        framework_agreement.update_signed_agreement_details_from_json(update_json['signedAgreementDetails'])
        framework_agreement.update_signed_agreement_details_from_json(
            {'frameworkAgreementVersion': framework_agreement_details['frameworkAgreementVersion']}
        )
        validate_agreement_details_data(
            framework_agreement.signed_agreement_details,
            enforce_required=True
        )

        user = User.query.filter(User.id == update_json['signedAgreementDetails']['uploaderUserId']).first()
        if not user:
            abort(400, "No user found with id '{}'".format(update_json['signedAgreementDetails']['uploaderUserId']))

    framework_agreement.signed_agreement_returned_at = datetime.utcnow()

    audit_event = AuditEvent(
        audit_type=AuditTypes.sign_agreement,
        user=updater_json['updated_by'],
        data=dict({
            'supplierId': framework_agreement.supplier_id,
            'frameworkSlug': framework_agreement.supplier_framework.framework.slug,
        }, **({'update': update_json} if update_json else {})),
        db_object=framework_agreement
    )

    try:
        db.session.add(framework_agreement)
        db.session.add(audit_event)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify(message="Database Error: {0}".format(e)), 400

    return jsonify(agreement=framework_agreement.serialize())
