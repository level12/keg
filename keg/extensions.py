try:
    import foobarbaz
except ImportError:
    foobarbaz = None

if foobarbaz:
    gettext = foobarbaz.gettext
    lazy_gettext = foobarbaz.lazy_gettext
    ngettext = foobarbaz.ngettext
    lazy_ngettext = foobarbaz.lazy_ngettext

else:
    def gettext(message, **variables):
        if not variables:
            return message

        return message.format(**variables)

    lazy_gettext = gettext

    def ngettext(singular, plural, num, **variables):
        variables.setdefault('num', num)

        return gettext(
            (
                singular
                if num == 1
                else plural
            ),
            **variables
        )

    lazy_ngettext = ngettext
