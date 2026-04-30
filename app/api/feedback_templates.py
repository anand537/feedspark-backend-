from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import afg_db
from app.models import FeedbackTemplate, User
from datetime import datetime

feedback_templates_api = Blueprint('feedback_templates_api', __name__, url_prefix='/feedback-templates')

@feedback_templates_api.route('/', methods=['GET'])
@jwt_required()
def get_feedback_templates():
    """Get all feedback templates"""
    # Optimization: Join with User to avoid N+1 query problem
    results = afg_db.session.query(FeedbackTemplate, User).outerjoin(User, FeedbackTemplate.created_by == User.id).all()
    result = []
    for template, creator in results:
        result.append({
            'id': str(template.id),
            'name': template.name,
            'template_text': template.template_text,
            'created_by': {
                'id': str(creator.id),
                'name': creator.name,
                'email': creator.email
            } if creator else None,
            'created_at': template.created_at.isoformat() if template.created_at else None
        })
    return jsonify(result)

@feedback_templates_api.route('/<uuid:template_id>', methods=['GET'])
@jwt_required()
def get_feedback_template(template_id):
    """Get a specific feedback template"""
    template = afg_db.session.get(FeedbackTemplate, template_id)
    if not template:
        return jsonify({'message': 'Feedback template not found'}), 404

    creator = afg_db.session.get(User, template.created_by) if template.created_by else None
    return jsonify({
        'id': str(template.id),
        'name': template.name,
        'template_text': template.template_text,
        'created_by': {
            'id': str(creator.id),
            'name': creator.name,
            'email': creator.email
        } if creator else None,
        'created_at': template.created_at.isoformat() if template.created_at else None
    })

@feedback_templates_api.route('/', methods=['POST'])
@jwt_required()
def create_feedback_template():
    """Create a new feedback template"""
    data = request.get_json()
    if not data or 'name' not in data or 'template_text' not in data:
        return jsonify({'message': 'Name and template_text are required'}), 400

    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    if current_user.role not in ['mentor', 'admin']:
        return jsonify({'message': 'Only mentors and admins can create templates'}), 403

    template = FeedbackTemplate(
        name=data['name'],
        template_text=data['template_text'],
        created_by=current_user_id,
        created_at=datetime.utcnow()
    )

    afg_db.session.add(template)
    afg_db.session.commit()

    return jsonify({
        'id': str(template.id),
        'name': template.name,
        'template_text': template.template_text,
        'created_by': str(template.created_by),
        'created_at': template.created_at.isoformat()
    }), 201

@feedback_templates_api.route('/<uuid:template_id>', methods=['PUT'])
@jwt_required()
def update_feedback_template(template_id):
    """Update a feedback template"""
    template = afg_db.session.get(FeedbackTemplate, template_id)
    if not template:
        return jsonify({'message': 'Feedback template not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)
    if current_user.role not in ['mentor', 'admin']:
        return jsonify({'message': 'Access denied'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    if 'name' in data:
        template.name = data['name']
    if 'template_text' in data:
        template.template_text = data['template_text']

    afg_db.session.commit()

    return jsonify({
        'id': str(template.id),
        'name': template.name,
        'template_text': template.template_text,
        'created_by': str(template.created_by),
        'created_at': template.created_at.isoformat() if template.created_at else None
    })

@feedback_templates_api.route('/<uuid:template_id>', methods=['DELETE'])
@jwt_required()
def delete_feedback_template(template_id):
    """Delete a feedback template"""
    template = afg_db.session.get(FeedbackTemplate, template_id)
    if not template:
        return jsonify({'message': 'Feedback template not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)
    if current_user.role not in ['mentor', 'admin']:
        return jsonify({'message': 'Access denied'}), 403

    afg_db.session.delete(template)
    afg_db.session.commit()

    return jsonify({'message': 'Feedback template deleted successfully'})
