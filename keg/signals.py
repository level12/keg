from flask.signals import Namespace

_signals = Namespace()

# Call when application initializations is completed.
# Sender will be the application instance.
app_ready = _signals.signal('app-ready')
config_ready = _signals.signal('config-ready')
testing_start = _signals.signal('testing-start')
