from __future__ import absolute_import
from __future__ import unicode_literals

import os.path as osp

import appdirs


def config_files(app):
    dirs = app.dirs

    config_fname = '{}.py'.format(app.import_name)

    dpaths = []
    if appdirs.system != 'win32':
        dpaths.extend(dirs.site_config_dir.split(':'))
        dpaths.append('/etc/{}'.format(app.import_name))
    else:
        dpaths.append(dirs.site_config_dir)
    dpaths.append(dirs.user_config_dir)

    fpaths = map(lambda dpath: osp.join(dpath, config_fname), dpaths)

    fpaths.append(osp.join(osp.dirname(app.root_path), '{}-config.py'.format(app.import_name)))

    return fpaths


class Default(object):
    # lock it down by default
    KEG_DIRS_MODE = 0o700
    KEG_ENDPOINTS = dict(
        home='public.home',
        login='public.home',
        after_login='public.home',
        after_logout='public.home',
    )


class Dev(object):
    DEBUG = True


class Test(object):
    DEBUG = True
    TESTING = True
