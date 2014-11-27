import os.path as osp
from setuptools import setup

cdir = osp.abspath(osp.dirname(__file__))
README = open(osp.join(cdir, 'readme.rst')).read()
CHANGELOG = open(osp.join(cdir, 'changelog.rst')).read()
VERSION = open(osp.join(cdir, 'keg', 'version.txt')).read().strip()

setup(
    name="Keg",
    version=VERSION,
    description="A web framework built on Flask & SQLAlchemy."
        "  Somewhere North of Flask but South of Django.",
    long_description='\n\n'.join((README, CHANGELOG)),
    author="Randy Syring",
    author_email="randy@thesyrings.us",
    url='http://bitbucket.org/level12/keg/',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
    ],
    license='BSD',
    packages=['keg'],
    zip_safe=False,
    include_package_data=True,
    install_requires=['appdirs'],
)
