Components
==========

Keg components follow the paradigm of flask extensions, and provide some defaults for the
purpose of setting up model/view structure. Using components, a project may be broken down into
logical blocks, each having their own entities, blueprints, templates, tests, etc.

* Components need to be registered in config at `KEG_REGISTERED_COMPONENTS`

  * The path given here should be a full dotted path to the top level of the component

    * e.g. `my_app.components.blog`

  * At the top level of the component, `__component__` must be defined as an instance of KegComponent

    * Depending on the needs of the component, model and view discovery may be driven by the subclasses
      of KegComponent that have path defaults
    * Examples:

      * `__component__ = KegModelComponent('blog')`
      * `__component__ = KegViewComponent('blog')`
      * `__component__ = KegModelViewComponent('blog')`

* Component discovery

  * A component will attempt to load model and blueprints on app init
  * The default paths relative to the component may be modified or extended on the component's definition
  * Default model path in "model" components: `.model.entities`

    * Override via the component's `db_visit_modules` list of relative import paths

  * Default blueprint path for "view" components: `.views.component_bp`

    * Use the `create_named_blueprint` or `create_blueprint` helpers on the component's `__component__`
      to create blueprints with configured template folders
    * Override via the component's `load_blueprints` list

      * List elements are a tuple of the relative import path and the name of the blueprint attribute

    * Components have their own template stores, in a `templates` folder

      * Override the component's template path via the `template_folder` attribute

  * Paths may also be supplied to the constructor

    * e.g. `__component__ = KegComponent('blog', db_visit_modules=('.somewhere.else', ))`

