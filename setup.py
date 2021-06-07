import os.path as osp
from setuptools import setup, find_packages

cdir = osp.abspath(osp.dirname(__file__))
README = open(osp.join(cdir, 'readme.rst')).read()
CHANGELOG = open(osp.join(cdir, 'changelog.rst')).read()

version_fpath = osp.join(cdir, 'keg', 'version.py')
version_globals = {}
with open(version_fpath) as fo:
    exec(fo.read(), version_globals)

setup(
    name="Keg",
    version=version_globals['VERSION'],
    description=("A web framework built on Flask & SQLAlchemy."
                 "  Somewhere North of Flask but South of Django."),
    long_description='\n\n'.join((README, CHANGELOG)),
    author="Randy Syring",
    author_email="randy.syring@level12.io",
    url='https://github.com/level12/keg',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    license='BSD',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'appdirs',
        'BlazeUtils',
        'blinker',
        'Click>=3.0',
        'Flask',
        'Flask-SQLAlchemy',
        'python-json-logger',
        'six',
        'sqlalchemy',
    ],
    extras_require={
        'tests': [
            'flask-webtest',
            'flask-wtf',
            "sqlalchemy_pyodbc_mssql; sys_platform == 'win32'",
            'pytest',
            'pytest-cov',
            'python-dotenv',
            'psycopg2-binary',
            'mock',
        ],
        'i18n': [
            'morphi>=0.2.0'
        ],
    }
)
