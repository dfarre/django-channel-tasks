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
    description='Running background tasks through REST API and websocket, with channels-redis',
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
    package_data={'django_tasks': ['templates/*', 'settings/channel-task-defaults.ini']},
    data_files=[('./channel-tasks-docker', ['docker-compose.yml',
                                            'Dockerfile',
                                            'setup-channel-tasks-docker.sh',
                                            'channel-tasks-unit.template.json']),
                ('./services', ['services/channel-tasks-docker.template.service',
                                'services/channel-tasks.template.service']),
                ('./bin', ['services/restart-channel-tasks-docker.sh',
                           'services/setup-channel-tasks.sh'])],
    entry_points={'console_scripts': ['channel-tasks-admin=django_tasks.entrypoint:manage_channel_tasks']},
    install_requires=[
        'Django', 'django-filter', 'django-extensions', 'django-request-logging', 'djangorestframework',
        'django-bootstrap-v5', 'channels', 'channels-redis', 'tzdata', 'psycopg2',
        'websocket-client'],
    extras_require={'dev': ['ipdb', 'ipython'],
                    'mypy': ['mypy', 'django-stubs', 'djangorestframework-stubs[compatible-mypy]',
                             'types-beautifulsoup4', 'types-setuptools'],
                    'test': tests_require},
    tests_require=tests_require,
)
