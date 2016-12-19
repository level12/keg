import keyring
import keg


try:
    import unittest.mock as mock
except ImportError:
    import mock


class MockKeyring(keyring.backend.KeyringBackend):
    priority = 1

    def __init__(self):
        self.passwords = dict()

    def set_password(self, servicename, username, password):
        key = '{}:{}'.format(servicename, username)
        self.passwords[key] = password

    def get_password(self, servicename, username):
        key = '{}:{}'.format(servicename, username)
        return self.passwords.get(key, username)

    def delete_password(self, servicename, username, password):
        pass


class TestKeyringManager:

    class MockApp:
        logger = mock.MagicMock()
        name = 'fake'

    def setup_method(self, _):
        self.manager = self.create_manager()

    def create_manager(self, app=MockApp, backend=MockKeyring):
        keyring.set_keyring(backend())
        return keg.keyring.Manager(app())

    def test_pattern_to_password(self):
        func = self.manager.pattern_to_password

        assert func('value') == 'value'
        assert func('${value}$') == 'value'
        assert func(b'${value}$') == b'value'
        assert func(b'${value}$:${other}$') == b'value:other'

    def test_substitute_finds_all_values_for_sub(self):
        data = {
            'no_ring': 'foo',
            'int_val': 1,
            'bool_val': True,
            'string_ring': '${string}$',
            'byte_ring': b'${bytes}$',
            'multi_string': '${multi_s_one}$:${multi_s_two}$',
            'multi_byte': b'${multi_b_one}$:${multi_b_two}$',
        }
        returned = self.manager.substitute(data)

        assert self.manager.sub_keys_seen == {'string', 'bytes', 'multi_s_one',
                                              'multi_s_two', 'multi_b_one',
                                              'multi_b_two'}
        assert returned['multi_byte'] == b'multi_b_one:multi_b_two'
        assert data == returned

    def test_ask_and_create(self):
        self.manager.secure_entry = lambda msg: 'password'

        self.manager.ask_and_create('key')
        assert keyring.get_password('fake', 'key') == 'password'

    def test_no_value_in_key_ring(self):
        class NoValueMockKeyring(MockKeyring):
            def get_password(self, servicename, username):
                return None

        manager = self.create_manager(backend=NoValueMockKeyring)
        manager.secure_entry = lambda msg: 'thing'

        data = manager.substitute(
            {'unknown': '${unknown}$'}
        )

        assert data['unknown'] == 'thing'
