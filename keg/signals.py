from __future__ import absolute_import

from flask.signals import Namespace

_signals = Namespace()

# Call when application initializations is completed.
# Sender will be the application instance.
app_ready = _signals.signal('app-ready')

config_ready = _signals.signal('config-ready')
testing_run_start = _signals.signal('testing-run-start')

db_clear_pre = _signals.signal('db-clear-pre')
db_clear_post = _signals.signal('db-clear-post')
db_init_pre = _signals.signal('db-init-pre')
db_init_post = _signals.signal('db-init-post')
