from flask import Blueprint, jsonify
from app.extensions import afg_db
from sqlalchemy import text
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Health check endpoint for load balancers and monitoring"""
    try:
        # Check database connection
        with afg_db.engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Check overall health
    overall_status = "healthy" if db_status == "healthy" else "unhealthy"

    return jsonify({
        "status": overall_status,
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200 if overall_status == "healthy" else 503
 