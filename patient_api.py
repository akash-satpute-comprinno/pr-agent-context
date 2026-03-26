"""
MedAI Patient History API
Handles retrieval of patient medical history and records
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import get_db_connection

logger = logging.getLogger(__name__)
patient_bp = Blueprint('patient', __name__)


@patient_bp.route('/api/patient/history', methods=['GET'])
@jwt_required()
def get_patient_history():
    """Get full patient medical history — requires JWT auth"""
    current_user = get_jwt_identity()
    patient_id = request.args.get('patient_id')

    # Validate input
    if not patient_id or not str(patient_id).isdigit():
        return jsonify({"error": "Invalid patient_id"}), 400

    # FIXED: parameterized query — no SQL injection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM patient_records WHERE patient_id = ?",
            (patient_id,)
        )
        records = cursor.fetchall()

    # FIXED: log only non-PII info
    logger.info(f"Patient history accessed by user={current_user}, patient_id={patient_id}, records={len(records)}")

    return jsonify({
        "patient_id": patient_id,
        "records": [dict(r) for r in records],
        "total": len(records)
    })


@patient_bp.route('/api/patient/update', methods=['POST'])
@jwt_required()
def update_patient():
    """Update patient information — requires JWT auth"""
    current_user = get_jwt_identity()
    data = request.get_json()

    # Validate required fields
    if not data or not all(k in data for k in ['id', 'name', 'phone']):
        return jsonify({"error": "Missing required fields"}), 400

    # FIXED: parameterized query — no SQL injection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE patients SET name = ?, phone = ? WHERE id = ?",
            (data['name'], data['phone'], data['id'])
        )
        conn.commit()

    # FIXED: log only non-PII info
    logger.debug(f"Patient record updated: id={data['id']} by user={current_user}")

    return jsonify({"status": "updated", "id": data['id']})
