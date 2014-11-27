import flask
import pathlib


# sentinal object
class NotGiven(object):
    pass


def ensure_dirs(newdir, mode=NotGiven):
    """
        A "safe" verision of Path.makedir(..., parents=True) that will only create the directory
        if it doesn't already exist.  We also manually create parents so that mode is set
        correctly.  Python docs say that mode is ignored when using Path.mkdir(..., parents=True)
    """
    if mode is NotGiven:
        mode = flask.current_app.config['KEG_DIRS_MODE']
    dpath = pathlib.Path(newdir)
    if dpath.is_dir():
        return
    if dpath.is_file():
        raise OSError("A file with the same name as the desired"
                      " directory, '{}', already exists.".format(dpath))
    ensure_dirs(dpath.parent, mode=mode)
    dpath.mkdir(mode)
