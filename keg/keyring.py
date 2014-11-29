from __future__ import absolute_import
from __future__ import unicode_literals

import getpass
import os
from pathlib import Path
import platform
import re
import sys

import keyring


class KeyringError(Exception):
    pass


class Manager(object):

    # regex that matches "${*}$" where * = any printable ascii character
    # that isn't "}"
    # see: http://www.catonmat.net/blog/my-favorite-regex/
    sub_pattern = '(\$\{([ -|~]+?)\}\$)'

    secretstorage_link_paths = [
        '/usr/lib/python2.7/dist-packages/dbus',
        '/usr/lib/python2.7/dist-packages/_dbus_bindings.so',
        '/usr/lib/python2.7/dist-packages/_dbus_glib_bindings.so',
        '/usr/lib/python2.7/dist-packages/secretstorage',
        '/usr/lib/python2.7/dist-packages/Crypto',
    ]

    backend_min_priority = 1

    def __init__(self, app):
        self.sub_re = re.compile(self.sub_pattern)
        self.log = app.logger
        self.app = app

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

    def venv_link_backend(self):
        if platform.system() != 'Linux':
            self.log.info('Keyring virtualenv setup only supports Linux for now.')
            return False

        venv_dpath = os.environ.get('VIRTUAL_ENV')
        if venv_dpath is None:
            self.log.warning('Trying to enable a keyring backend, but not not in a virtualenv.')
            return False

        venv_site_packages = os.path.join(venv_dpath, 'lib', 'python%s' % sys.version[:3],
                                          'site-packages')

        return self.venv_link_secretstorage(venv_site_packages)

    def venv_link_secretstorage(self, target_dir):
        for dbus_fpath in self.secretstorage_link_paths:
            dbus_fpath = Path(dbus_fpath)
            if not dbus_fpath.exists():
                return False
            target_dbus_fpath = Path(target_dir, dbus_fpath.name)
            if not target_dbus_fpath.exists():
                target_dbus_fpath.symlink_to(dbus_fpath)

        try:
            # this will throw an exception of all the dependencies didn't get setup correctly
            import secretstorage
            bus = secretstorage.dbus_init()
            list(secretstorage.get_all_collections(bus))
            self.log.info('Succesfully linked files and the SecretService keyring is now setup.')
        except Exception:
            self.log.exception('')
            self.log.error('failed setting up secretstorage for the SecretService keyring')
            return False

    def substitute(self, data):
        if not self.verify_backend():
            return

        for key in data.keys():
            value = data[key]
            if not isinstance(value, basestring):
                continue
            matches = self.sub_re.finditer(value)
            for match in matches:
                replace_this = match.group(1)
                keyring_key = match.group(2)

                self.log.debug('keyring substittue: replacing {0} for data key "{1}"'
                               .format(replace_this, key))

                # reassign value for cases when there is more than one keyring replacement
                # needed in a config value
                value = data[key]

                keyring_value = keyring.get_password(self.app.name, keyring_key)
                if keyring_value is None:
                    keyring_value = getpass.getpass('Enter value for "{0}": '.format(keyring_key))
                    keyring.set_password(self.app.name, keyring_key, keyring_value)
                data[key] = value.replace(replace_this, keyring_value, 1)

