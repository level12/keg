from __future__ import absolute_import

import os.path as osp

import appdirs
from blazeutils.helpers import tolist
import flask
from pathlib import PurePath
import six
from werkzeug.utils import (
    import_string,
    ImportStringError
)

from keg.utils import app_environ_get, pymodule_fpaths_to_objects


class ConfigurationError(Exception):
    pass


class SubstituteValue(object):
    def __init__(self, value):
        self.value = value


substitute = SubstituteValue


class Config(flask.Config):
    default_config_locations = [
        # Keg's defaults
        'keg.config.DefaultProfile',
        # Keg's defaults for the selected profile
        'keg.config.{profile}',
        # App defaults for all profiles
        '{app_import_name}.config.DefaultProfile',
        # apply the profile specific defaults that are in the app's config file
        '{app_import_name}.config.{profile}',
    ]

    def from_obj_if_exists(self, obj_location):
        try:
            self.from_object(obj_location)
            self.configs_found.append(obj_location)
        except ImportStringError as e:
            if obj_location not in str(e):
                raise

    def default_config_locations_parsed(self):
        retval = []
        for location in self.default_config_locations:
            # if no profile is given, the location want's one, that location isn't valid
            if '{profile}' in location and self.profile is None:
                continue

            retval.append(location.format(app_import_name=self.app_import_name,
                                          profile=self.profile))
        return retval

    def init_app(self, app_config_profile, app_import_name, app_root_path, use_test_profile,
                 config_file_objs=None):
        self.use_test_profile = use_test_profile
        self.profile = app_config_profile
        self.dirs = appdirs.AppDirs(app_import_name, appauthor=False, multipath=True)
        self.app_import_name = app_import_name
        self.app_root_path = app_root_path

        if config_file_objs:
            self.config_file_objs = config_file_objs
        else:
            possible_config_fpaths = self.config_file_paths()
            self.config_file_objs = pymodule_fpaths_to_objects(possible_config_fpaths)

        if self.profile is None:
            self.profile = self.determine_selected_profile()

        self.configs_found = []

        for dotted_location in self.default_config_locations_parsed():
            dotted_location = dotted_location.format(app_import_name=app_import_name,
                                                     profile=self.profile)
            self.from_obj_if_exists(dotted_location)

        # apply settings from any of this app's configuration files
        for fpath, objects in self.config_file_objs:
            if self.profile in objects:
                self.from_object(objects[self.profile])
                self.configs_found.append('{}:{}'.format(fpath, self.profile))

        sub_values = self.substitution_values()
        self.substitution_apply(sub_values)

    def config_file_paths(self):
        dirs = self.dirs

        config_fname = '{}-config.py'.format(self.app_import_name)

        dpaths = []
        if appdirs.system != 'win32':
            dpaths.extend(dirs.site_config_dir.split(':'))
            dpaths.append('/etc/{}'.format(self.app_import_name))
            dpaths.append('/etc')
        else:
            system_drive = PurePath(dirs.site_config_dir).drive
            system_etc_dir = PurePath(system_drive, '/', 'etc')
            dpaths.extend((
                dirs.site_config_dir,
                system_etc_dir.joinpath(self.app_import_name).__str__(),
                system_etc_dir.__str__()
            ))
        dpaths.append(dirs.user_config_dir)
        dpaths.append(osp.dirname(self.app_root_path))

        fpaths = [osp.join(dpath, config_fname) for dpath in dpaths]

        return fpaths

    def email_error_to(self):
        error_to = self.get('KEG_EMAIL_ERROR_TO')
        override_to = self.get('KEG_EMAIL_OVERRIDE_TO')
        if override_to:
            return tolist(override_to)
        return tolist(error_to)

    def determine_selected_profile(self):
        # if we find the value in the environment, use it
        profile = app_environ_get(self.app_import_name, 'CONFIG_PROFILE')
        if profile is not None:
            return profile

        use_test_profile = app_environ_get(self.app_import_name, 'USE_TEST_PROFILE', '')
        if use_test_profile.strip() or self.use_test_profile:
            return 'TestProfile'

        # look for it in the app's main config file (e.g. myapp.config)
        app_config = import_string('{}.config'.format(self.app_import_name), silent=True)
        if app_config and hasattr(app_config, 'DEFAULT_PROFILE'):
            profile = app_config.DEFAULT_PROFILE

        # Look for it in all the config files found.  This loops from lowest-priority config file
        # to highest priority, so the last file found with a value is kept.  Accordingly, any app
        # specific file has priority over the app's main config file, which could be set just above.
        for fpath, objects in self.config_file_objs:
            if 'DEFAULT_PROFILE' in objects:
                profile = objects['DEFAULT_PROFILE']

        return profile

    def substitution_values(self):
        return dict(
            user_log_dir=self.dirs.user_log_dir,
            app_import_name=self.app_import_name,
        )

    def substitution_apply(self, sub_values):
        for config_key, config_value in self.items():
            if not isinstance(config_value, SubstituteValue):
                continue
            new_value = config_value.value.format(**sub_values)
            self[config_key] = new_value


# The following three classes are default configuration profiles
class DefaultProfile(object):
    KEG_DIR_MODE = 0o777
    KEG_ENDPOINTS = dict(
        home='public.home',
        login='public.home',
        after_login='public.home',
        after_logout='public.home',
    )

    KEG_KEYRING_ENABLE = True

    KEG_SMTP_HOST = 'localhost'

    KEG_DB_DIALECT_OPTIONS = {}


class DevProfile(object):
    DEBUG = True


class TestProfile(object):
    DEBUG = True
    TESTING = True
    KEG_KEYRING_ENABLE = False
    KEG_LOG_SYSLOG_ENABLED = False

    # set this to allow generation of URLs without a request context
    SERVER_NAME = 'keg.example.com' if six.PY3 else b'keg.example.com'

    # simple value for testing is fine
    SECRET_KEY = '12345'

    # Sane default values for testing to get rid of warnings.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
