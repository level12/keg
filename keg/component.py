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
    any blueprints specified by `load_blueprints`.

    Blueprints can be created with the helper methods `create_named_blueprint` or `create_blueprint`
    in order to have a configured template folder relative to the blueprint path.

    Use KegModelComponent, KegViewComponent, or KegModelViewComponent for some helpful defaults for
    model/blueprint discovery.

    db_visit_modules: an iterable of dotted paths (e.g. `.mycomponent.entities`,
                      `app.component.extraentities`) where Keg can find the entities for this
                      component to load them into the metadata.

    .. note:: Normally this is not explicitly required but can be useful in cases where imports
       won't reach that file.

    .. note:: This can accept relative dotted paths (starts with `.`) and it will prepend the
       component python package determined by Keg when instantiating the component. You can also
       pass absolute dotted paths and no alterations will be performed.

    load_blueprints: an iterable of tuples, each having a dotted path (e.g. `.mycomponent.views`,
                     `app.component.extraviews`) and the blueprint attribute name to load and
                     register on the app. E.g. `(('.views', 'component_bp'), )`

    .. note:: This can accept relative dotted paths (starts with `.`) and it will prepend the
       component python package determined by Keg when instantiating the component. You can also
       pass absolute dotted paths and no alterations will be performed.

    template_folder: string to be passed for template config to blueprints created via the component
    """
    db_visit_modules = tuple()
    load_blueprints = tuple()
    template_folder = 'templates'

    def __init__(self, name, app=None, db_visit_modules=None, load_blueprints=None,
                 template_folder=None, parent_path=None):
        self.name = name
        # Allow customization of the defaults in the constructor
        self.db_visit_modules = db_visit_modules or self.db_visit_modules
        self.load_blueprints = load_blueprints or self.load_blueprints
        self.template_folder = template_folder or self.template_folder
        if app:
            # Not really intended to be used this way, but it fits the flask extension paradigm
            # and could conceivably be set up in lieu of KEG_REGISTERED_COMPONENTS
            self.init_app(app, parent_path=parent_path)

    def init_app(self, app, parent_path=None):
        # parent_path gets used as an absolute parent for the relative import paths of
        # model/blueprints.
        # E.g. if relative_dotted_path is `my_app.components.widget` and one of the relative import
        # paths is `.model.entities`, the full import is `my_app.components.widget.model.entities`
        self.init_config(app)
        self.init_db(parent_path)
        self.init_blueprints(app, parent_path)

    def init_config(self, app):
        # Components may define their own config defaults
        pass

    def init_db(self, parent_path):
        # Intent is to import the listed modules, so their entities are registered in metadata
        for dotted_path in self.db_visit_modules:
            import_name = dotted_path
            if import_name.startswith('.'):
                import_name = f'{parent_path}{dotted_path}'
            importlib.import_module(import_name)

    def init_blueprints(self, app, parent_path):
        # Register any blueprints that are listed by path in load_blueprints
        for bp_path, bp_attr in self.load_blueprints:
            import_name = bp_path
            if import_name.startswith('.'):
                import_name = f'{parent_path}{bp_path}'
            mod_imported = importlib.import_module(import_name)
            app.register_blueprint(getattr(mod_imported, bp_attr))

    def create_blueprint(self, *args, **kwargs):
        """Make a flask blueprint having a template folder configured.

        Generally, args and kwargs provided will be passed to the blueprint constructor, with
        the following exceptions:

        - template_folder kwarg defaults to the component's template_folder if not provided
        - blueprint_cls kwarg may be used to specify an alternative to flask.Blueprint
        """
        kwargs['template_folder'] = kwargs.get('template_folder', self.template_folder)
        blueprint_cls = kwargs.pop('blueprint_cls', flask.Blueprint)
        bp = blueprint_cls(*args, **kwargs)

        return bp

    def create_named_blueprint(self, *args, **kwargs):
        # Make a flask blueprint named with the component name, having a template folder configured
        return self.create_blueprint(self.name, *args, **kwargs)


class ModelMixin:
    db_visit_modules = ('.model.entities', )


class ViewMixin:
    load_blueprints = (('.views', 'component_bp'), )


class KegModelComponent(ModelMixin, KegComponent):
    pass


class KegViewComponent(ViewMixin, KegComponent):
    pass


class KegModelViewComponent(ModelMixin, ViewMixin, KegComponent):
    pass
