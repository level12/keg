from __future__ import absolute_import

import getpass
import re
import sys
import itertools

import six

try:
    import keyring
except ImportError:
    keyring = None


class KeyringError(Exception):
    pass


class MissingValueError(Exception):

    def __init__(self, key):
        self.key = key

        super(Exception, self).__init__("No value for {} found in key "
                                        "ring".format(key))


class Manager(object):

    # regex that matches "${*}$" where * = any printable ASCII character
    # that isn't "}"
    # see: http://www.catonmat.net/blog/my-favorite-regex/
    sub_pattern = '(\$\{([ -|~]+?)\}\$)'

    backend_min_priority = 1

    def __init__(self, app, service_name=None, secure_entry=getpass.getpass):
        self.sub_re = re.compile(self.sub_pattern)
        self.log = app.logger
        self.app = app
        self.service_name = service_name or self.app.name
        self.sub_keys_seen = set()
        self.secure_entry = secure_entry

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

    def pattern_to_password(self, value, service_name=None):
        """
        Substitutes a configuration value which matches self.sub_pattern with
        the value from the keyring.

        :param value: the substitutable value '${value}$'
        :param service_name: a configured keyring service name
        """
        if not isinstance(value, (six.binary_type, six.text_type)):
            return value

        # preserve the original type so that we can convert at the end
        is_bytes = isinstance(value, six.binary_type)
        service = service_name or self.service_name

        # Convert to a regular string if it is bytes else use as is
        value = value.decode() if is_bytes else value

        # Find all the possible keys we need to look up. Some values need
        # multiple replacements, for example '${user}$:${pass}$'. Therefore
        # this loop will run once for each match i.e. user and pass
        for match in self.sub_re.finditer(value):
            raw = match.group(1)  # '${user}$'
            clean = match.group(2)  # user

            # TODO (NZ): I am not really wild about this being here, but I don't
            # have a good way of keeping the data without it.
            self.sub_keys_seen.add(clean)

            if self.log:
                msg = 'Keyring Substitute: replacing {} for key {}'
                self.log.debug(msg.format(raw, clean))

            stored_value = keyring.get_password(service, clean)
            if not stored_value:
                raise MissingValueError(clean)

            value = value.replace(raw, stored_value, 1)

        return value.encode() if is_bytes else value

    def substitute(self, data):
        if not self.verify_backend():
            return

        def key_and_value(key, value):
            try:
                password = self.pattern_to_password(value)
            except MissingValueError as err:
                # Backwards comp... Ask for the value if we can't find it.
                #
                # TODO: Remove the need to ask for a password in this method
                # instead the substitute should work on known values and setting
                # values should be a different function
                password = self.ask_and_create(err.key)

            return key, password

        # Rifle through the dictionary, substitute where necessary
        subbed = {key: value for key, value in
                  itertools.starmap(key_and_value, six.iteritems(data))}

        # Mutate the data passed in for backwards comp.
        # TODO: Remove this mutation and just return the data allowing the
        # caller to decide what to do with it.
        data.update(subbed)
        return subbed

    def delete(self, key):
        keyring.delete_password(self.app.name, key)

    def create(self, key, value, service_name=None):
        keyring.set_password(service_name or self.service_name, key, value)

    def ask_and_create(self, key, service_name=None):
        msg = 'Missing secret for "{0}": '.format(key)

        # Windows getpass implementation breaks in Python2 when passing it Unicode
        if sys.version_info < (3,) and sys.platform.startswith('win'):
            msg = str(msg)

        value = self.secure_entry(msg)
        self.create(key, value, service_name)

        return value
