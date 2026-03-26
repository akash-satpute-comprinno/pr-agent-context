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
@jwt_required()  # FIXED: JWT authentication required
def get_patient_history():
    """Get full patient medical history"""
    current_user = get_jwt_identity()
    patient_id = request.args.get('patient_id')

    # BUG: SQL injection still present
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM patient_records WHERE patient_id = '" + str(patient_id) + "'"
    cursor.execute(query)
    records = cursor.fetchall()
    conn.close()

    # BUG: PII still being logged in plain text
    for record in records:
        logger.info(f"Patient record accessed: name={record['name']}, "
                    f"phone={record['phone']}, diagnosis={record['diagnosis']}, "
                    f"prescription={record['prescription']}")

    return jsonify({
        "patient_id": patient_id,
        "records": [dict(r) for r in records],
        "total": len(records)
    })


@patient_bp.route('/api/patient/update', methods=['POST'])
def update_patient():
    """Update patient information"""
    data = request.get_json()

    # BUG: No authentication, no input validation
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE patients SET name='" + data['name'] +
        "', phone='" + data['phone'] +
        "' WHERE id=" + str(data['id'])
    )
    conn.commit()
    conn.close()

    # BUG: Logging sensitive update data
    logger.debug(f"Patient updated: {data}")

    return jsonify({"status": "updated", "patient": data})
