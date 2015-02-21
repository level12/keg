from __future__ import absolute_import
from __future__ import unicode_literals

import os.path as osp

import appdirs
from blazeutils.helpers import tolist
import flask
from pathlib import PurePath
from werkzeug.utils import ImportStringError

import keg.compat as compat
from keg.utils import app_environ_get, pymodule_fpaths_to_objects


class ConfigurationError(Exception):
    pass


class Config(flask.Config):
    default_config_locations = [
        # Keg's defaults
        'keg.config.DefaultProfile',
        # Keg's defaults for the selected profile
        'keg.config.{profile}'
        # App defaults for all profiles
        '{app_import_name}.config.DefaultProfile'
        # apply the profile specific defaults that are in the app's config file
        '{app_import_name}.config.{profile}'
    ]

    def from_obj_if_exists(self, obj_location):
        try:
            self.from_object(obj_location)
            self.configs_found.append(obj_location)
        except ImportStringError as e:
            if obj_location not in str(e):
                raise

    def init_app(self, app_config_profile, app_import_name, app_root_path, config_file_objs=None):
        self.profile = app_config_profile
        self.dirs = appdirs.AppDirs(app_import_name, appauthor=False, multipath=True)

        if config_file_objs:
            self.config_file_objs = config_file_objs
        else:
            possible_config_fpaths = self.config_file_paths(app_import_name, app_root_path)
            self.config_file_objs = pymodule_fpaths_to_objects(possible_config_fpaths)

        if self.profile is None:
            self.profile = self.determine_selected_profile(app_import_name)

        self.configs_found = []

        for dotted_location in self.default_config_locations:
            dotted_location = dotted_location.format(app_import_name=app_import_name,
                                                     profile=self.profile)
            self.from_obj_if_exists(dotted_location)

        # apply settings from any of this app's configuration files
        for fpath, objects in self.config_file_objs:
            if self.profile in objects:
                self.from_object(objects[self.profile])
                self.configs_found.append('{}:{}'.format(fpath, self.profile))

    def config_file_paths(self, app_import_name, app_root_path):
        dirs = self.dirs

        config_fname = '{}-config.py'.format(app_import_name)

        dpaths = []
        if appdirs.system != 'win32':
            dpaths.extend(dirs.site_config_dir.split(':'))
            dpaths.append('/etc/{}'.format(app_import_name))
            dpaths.append('/etc')
        else:
            system_drive = PurePath(dirs.site_config_dir).drive
            system_etc_dir = PurePath(system_drive, '/', 'etc')
            dpaths.extend((
                dirs.site_config_dir,
                system_etc_dir.joinpath(app_import_name).__str__(),
                system_etc_dir.__str__()
            ))
        dpaths.append(dirs.user_config_dir)
        dpaths.append(osp.dirname(app_root_path))

        fpaths = map(lambda dpath: osp.join(dpath, config_fname), dpaths)

        return fpaths

    def email_error_to(self):
        error_to = self.get('KEG_EMAIL_ERROR_TO')
        override_to = self.get('KEG_EMAIL_OVERRIDE_TO')
        if override_to:
            return tolist(override_to)
        return tolist(error_to)

    def determine_selected_profile(self, app_import_name):
        # if we find the value in the environment, use it
        profile = app_environ_get(app_import_name, 'CONFIG_PROFILE')
        if profile is not None:
            return profile

        # look for it in all the config files found
        for fpath, objects in self.config_file_objs:
            if 'DEFAULT_PROFILE' in objects:
                profile = objects['DEFAULT_PROFILE']

        return profile


# The following three classes are default configuration profiles
class DefaultProfile(object):
    # lock it down by default
    KEG_DIRS_MODE = 0o700
    KEG_ENDPOINTS = dict(
        home='public.home',
        login='public.home',
        after_login='public.home',
        after_logout='public.home',
    )
    KEG_KEYRING_ENABLE = True

    KEG_SMTP_HOST = 'localhost'


class DevProfile(object):
    DEBUG = True


class TestProfile(object):
    DEBUG = True
    TESTING = True
