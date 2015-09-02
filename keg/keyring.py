from __future__ import absolute_import
from __future__ import unicode_literals

import getpass
import re
import sys

import six

try:
    import keyring
except ImportError:
    keyring = None


class KeyringError(Exception):
    pass


class Manager(object):

    # regex that matches "${*}$" where * = any printable ascii character
    # that isn't "}"
    # see: http://www.catonmat.net/blog/my-favorite-regex/
    sub_pattern = '(\$\{([ -|~]+?)\}\$)'

    backend_min_priority = 1

    def __init__(self, app):
        self.sub_re = re.compile(self.sub_pattern)
        self.log = app.logger
        self.app = app
        self.sub_keys_seen = set()

        if not self.verify_backend():
            self.log.warning(
                'Insecure keyring backend detected, keyring substitution unavailable. '
                'Run this app\'s keyring command for more info.'
            )

    def verify_backend(self):
        backend = keyring.get_keyring()
        if backend.priority < self.backend_min_priority:
            return False
        return True

    def substitute(self, data):
        if not self.verify_backend():
            return

        for key in data.keys():
            value = data[key]
            if not isinstance(value, six.string_types):
                continue
            matches = self.sub_re.finditer(value)
            for match in matches:
                replace_this = match.group(1)
                keyring_key = match.group(2)

                self.sub_keys_seen.add(keyring_key)

                self.log.debug('keyring substitute: replacing {0} for data key "{1}"'
                               .format(replace_this, key))

                # reassign value for cases when there is more than one keyring replacement
                # needed in a config value
                value = data[key]

                keyring_value = keyring.get_password(self.app.name, keyring_key)
                if keyring_value is None:
                    msg = 'Enter value for "{0}": '.format(keyring_key)
                    # Windows getpass implementation breaks in Python2 when passing it unicode
                    if sys.version_info < (3,) and sys.platform.startswith('win'):
                        msg = str(msg)
                    keyring_value = getpass.getpass(msg)
                    keyring.set_password(self.app.name, keyring_key, keyring_value)
                data[key] = value.replace(replace_this, keyring_value, 1)

    def delete(self, key):
        keyring.delete_password(self.app.name, key)
