
DEFAULT_PROFILE = 'ConfigFileDefaultProfile'


class ConfigFileDefaultProfile(object):
    PROFILE_FROM = 'config-file-default'


class AppInitProfile(object):
    PROFILE_FROM = 'app-init'


class TestProfile(object):
    PROFILE_FROM = 'testing-default'


class EnvironmentProfile(object):
    PROFILE_FROM = 'environment'


class CLIOption(object):
    PROFILE_FROM = 'cli-option'
