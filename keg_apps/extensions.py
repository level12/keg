from morphi.messages import Manager
from morphi.registry import default_registry

translation_manager = Manager(package_name='keg_apps')
default_registry.subscribe(translation_manager)

gettext = translation_manager.gettext
lazy_gettext = translation_manager.lazy_gettext
lazy_ngettext = translation_manager.lazy_ngettext
ngettext = translation_manager.ngettext
