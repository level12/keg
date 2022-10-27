from flask.signals import Namespace

_signals = Namespace()

# Call when application initializations is completed.
# Sender will be the application instance.
init_complete = _signals.signal('init-complete')
# Will deprecate app-ready eventually
app_ready = _signals.signal('app-ready')

# Same signals.  Will deprecate config_ready eventually.
config_ready = _signals.signal('config-ready')
config_complete = _signals.signal('config-complete')

# Call when db init_app complete, before any models are visited.
# Note that when this called, app setup is not complete. db is
# the first extension set up, so other extensions, app.visit_modules,
# etc. will not be available.
# Ideal for setting metadata properties.
db_before_import = _signals.signal('db-before-import')

testing_run_start = _signals.signal('testing-run-start')

db_clear_pre = _signals.signal('db-clear-pre')
db_clear_post = _signals.signal('db-clear-post')
db_init_pre = _signals.signal('db-init-pre')
db_init_post = _signals.signal('db-init-post')
