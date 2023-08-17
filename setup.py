import configparser
import setuptools


ini = configparser.ConfigParser()
ini.read('version.ini')


with open('README.md') as readme:
    long_description = readme.read()


tests_require = ['pytest', 'pytest-cov', 'pytest-django', 'pytest-asyncio', 'beautifulsoup4',
                 'bdd-coder==2.2.3.dev2']

setuptools.setup(
    name=ini['version']['name'],
    version=ini['version']['value'],
    author='Daniel Farré Manzorro',
    author_email='d.farre.m@gmail.com',
    description='Running background tasks trhough REST API and websocket, with channels-redis',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://bitbucket.org/coleopter/django-tasks',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers'],
    packages=setuptools.find_packages(),
    install_requires=[
        'Django', 'django-filter', 'django-extensions', 'django-request-logging', 'djangorestframework',
        'django-bootstrap-v5', 'channels', 'channels-redis', 'daphne', 'tzdata', 'psycopg2-binary',
        'websocket-client'],
    extras_require={'dev': ['ipdb', 'ipython'],
                    'mypy': ['mypy', 'django-stubs', 'djangorestframework-stubs[compatible-mypy]'],
                    'test': tests_require},
    tests_require=tests_require
)
