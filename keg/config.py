from __future__ import absolute_import
from __future__ import unicode_literals

import os.path as osp

import appdirs
from blazeutils.helpers import tolist
import flask
import keg.compat as compat
from pathlib import PurePath


class ConfigurationError(Exception):
    pass


class Config(flask.Config):

    def config_files(self, app):
        dirs = app.dirs

        config_fname = '{}-config.py'.format(app.import_name)

        dpaths = []
        if appdirs.system != 'win32':
            dpaths.extend(dirs.site_config_dir.split(':'))
            dpaths.append('/etc/{}'.format(app.import_name))
            dpaths.append('/etc')
        else:
            system_drive = PurePath(dirs.site_config_dir).drive
            system_etc_dir = PurePath(system_drive, '/', 'etc')
            dpaths.extend((
                dirs.site_config_dir,
                system_etc_dir.joinpath(app.import_name).__str__(),
                system_etc_dir.__str__()
            ))
        dpaths.append(dirs.user_config_dir)
        dpaths.append(osp.dirname(app.root_path))

        fpaths = map(lambda dpath: osp.join(dpath, config_fname), dpaths)

        return fpaths

    def email_error_to(self):
        error_to = self.get('KEG_EMAIL_ERROR_TO')
        override_to = self.get('KEG_EMAIL_OVERRIDE_TO')
        if override_to:
            return tolist(override_to)
        return tolist(error_to)

    def find_default_profile(self, app):
        # if we find the value in the environment, use it
        profile = app.environ_get('CONFIG_PROFILE')
        if profile is not None:
            return profile

        # look for it in all the config files
        possible_config_files = self.config_files(app)
        for fpath in possible_config_files:
            if osp.isfile(fpath):
                default_profile = compat.object_from_source(fpath, 'DEFAULT_PROFILE')
                if default_profile:
                    profile = default_profile
        return profile


# The following three classes are default configuration profiles
class Default(object):
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


class Dev(object):
    DEBUG = True


class Test(object):
    DEBUG = True
    TESTING = True
