import importlib

import flask


class KegComponent:
    """ Keg components follow the paradigm of flask extensions, and provide some defaults for the
    purpose of setting up model/view structure. Using components, a project may be broken down into
    logical blocks, each having their own entities, blueprints, templates, tests, etc.

    Setup involves:
    - KEG_REGISTERED_COMPONENTS config setting: assumed to be an iterable of importable dotted paths
    - `__component__`: at the top level of each dotted path, this attribute should point to an
    instance of `KegComponent`. E.g. `__component__ = KegComponent('widgets')`

    By default, components will load entities from `db_visit_modules` into metadata and register
    any blueprints specified by `blueprints`.

    Blueprints can be created with the helper methods `get_named_blueprint` or `get_blueprint` in
    order to have a configured template folder relative to the blueprint path.
    """
    db_visit_modules = ['.model.entities']
    blueprints = [('.views', 'component_bp')]
    template_folder = 'templates'

    def __init__(self, name, app=None, db_visit_modules=None, blueprints=None,
                 template_folder=None):
        self.name = name
        # This gets used as an absolute parent for the relative import paths of model/blueprints
        self.relative_dotted_path = ''
        # Allow customization of the defaults in the constructor
        self.db_visit_modules = db_visit_modules or self.db_visit_modules
        self.blueprints = blueprints or self.blueprints
        self.template_folder = template_folder or self.template_folder
        if app:
            # Not really intended to be used this way, but it fits the flask extension paradigm
            # and could conceivably be set up in lieu of KEG_REGISTERED_COMPONENTS
            self.init_app(app)

    def set_dotted_path(self, dotted_path):
        # The Keg app sets this when following KEG_REGISTERED_COMPONENTS
        self.relative_dotted_path = dotted_path

    def init_app(self, app):
        self.init_db()
        self.init_blueprints(app)

    def init_db(self):
        # Intent is to import the listed modules, so their entities are registered in metadata
        # Note: check the import error, if there is one, so that import errors in the model
        # modules themselves do not fail silently
        for dotted_path in self.db_visit_modules:
            import_name = f'{self.relative_dotted_path}{dotted_path}'
            try:
                importlib.import_module(import_name)
            except ModuleNotFoundError as exc:
                if not import_name.startswith(str(exc).split('\'')[1]):
                    raise

    def init_blueprints(self, app):
        # Note: check the import error, if there is one, so that import errors in the view
        # modules themselves do not fail silently
        for bp_path, bp_attr in self.blueprints:
            import_name = f'{self.relative_dotted_path}{bp_path}'
            try:
                mod_imported = importlib.import_module(import_name)
            except ModuleNotFoundError as exc:
                if not import_name.startswith(str(exc).split('\'')[1]):
                    raise
            else:
                if hasattr(mod_imported, bp_attr):
                    app.register_blueprint(getattr(mod_imported, bp_attr))

    def get_blueprint(self, *args, **kwargs):
        # Get a flask blueprint having a template folder configured
        kwargs['template_folder'] = kwargs.get('template_folder', self.template_folder)
        bp = flask.Blueprint(*args, **kwargs)

        return bp

    def get_named_blueprint(self, *args, **kwargs):
        # Get a flask blueprint named with the component name, having a template folder configured
        return self.get_blueprint(self.name, *args, **kwargs)
