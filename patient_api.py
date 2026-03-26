"""
MedAI Patient History API
Handles retrieval of patient medical history and records.
All endpoints require JWT authentication and role-based authorization.
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import get_db_connection

# Configure logging — no PII in log output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
patient_bp = Blueprint('patient', __name__)

ALLOWED_ROLES = {'doctor', 'admin', 'nurse'}


def _get_user_role(user_identity: dict) -> str:
    """Extract role from JWT identity"""
    return user_identity.get('role', '') if isinstance(user_identity, dict) else ''


@patient_bp.route('/api/patient/history', methods=['GET'])
@jwt_required()
def get_patient_history():
    """Get patient medical history — requires JWT auth + authorized role"""
    current_user = get_jwt_identity()
    role = _get_user_role(current_user)

    if role not in ALLOWED_ROLES:
        return jsonify({"error": "Unauthorized — insufficient permissions"}), 403

    patient_id = request.args.get('patient_id')
    if not patient_id or not str(patient_id).isdigit():
        return jsonify({"error": "Invalid patient_id"}), 400

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM patient_records WHERE patient_id = ?",
            (int(patient_id),)
        )
        records = cursor.fetchall()

    # AC-2: No PII logged — name, phone, diagnosis, patient_id intentionally excluded
    logger.info("Patient history accessed by role=%s", role)

    return jsonify({
        "patient_id": patient_id,
        "records": [dict(r) for r in records],
        "total": len(records)
    })


@patient_bp.route('/api/patient/update', methods=['POST'])
@jwt_required()
def update_patient():
    """Update patient information — requires JWT auth + authorized role"""
    current_user = get_jwt_identity()
    role = _get_user_role(current_user)

    if role not in ALLOWED_ROLES:
        return jsonify({"error": "Unauthorized — insufficient permissions"}), 403

    data = request.get_json()
    if not data or not all(k in data for k in ['id', 'name', 'phone']):
        return jsonify({"error": "Missing required fields: id, name, phone"}), 400

    if not str(data['id']).isdigit():
        return jsonify({"error": "Invalid patient id"}), 400

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE patients SET name = ?, phone = ? WHERE id = ?",
            (data['name'], data['phone'], int(data['id']))
        )
        conn.commit()

    # AC-2: No PII logged — id, name, phone intentionally excluded
    logger.info("Patient record updated by role=%s", role)

    return jsonify({"status": "updated", "id": data['id']})
