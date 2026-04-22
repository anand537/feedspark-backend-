from flasgger import Swagger

def init_swagger(app):
    """
    Initialize Flasgger for OpenAPI/Swagger documentation.
    """
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,  # all in
                "model_filter": lambda tag: True,  # all in
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": app.config.get('SWAGGER', {}).get('specs_route', '/apidocs/')
    }
    
    template = {
        "openapi": "3.0.2",
        "info": {
            "title": app.config.get('SWAGGER', {}).get('title', 'API'),
            "description": "API documentation for the Auto-Feedback Generator backend.",
            "version": "1.0.0"
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        },
        "security": [
            {
                "bearerAuth": []
            }
        ]
    }

    return Swagger(app, config=swagger_config, template=template)