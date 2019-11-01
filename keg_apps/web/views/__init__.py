from .routing import blueprint as routing_bp
from .templating import blueprint as blueprint_bp
from .other import blueprint as other_bp
from .custom import blueprint as custom_bp

all_blueprints = [routing_bp, blueprint_bp, other_bp, custom_bp]
