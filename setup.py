import configparser
import setuptools


ini = configparser.ConfigParser()
ini.read('version.ini')


with open('README.md') as readme:
    long_description = readme.read()


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
    package_data={'django_tasks': [
        'templates/task_alerts.html', 'templates/admin/base.html', 'static/css/bootstrap-isolated.min.css',
    ]},
    data_files=[('./channel-tasks-docker', ['docker-compose.yml',
                                            'Dockerfile',
                                            'setup-channel-tasks-docker.sh',
                                            'channel-tasks-unit.template.json']),
                ('./channel-tasks-unit', ['services/nginx-unit/application.template.json',
                                          'services/nginx-unit/listener.template.json',
                                          'services/nginx-unit/routes.template.json']),
                ('./channel-tasks-services', ['services/channel-tasks-docker.template.service',
                                              'services/channel-tasks.template.service']),
                ('./bin', ['services/restart-channel-tasks-docker.sh',
                           'services/setup-channel-tasks.sh'])],
    entry_points={'console_scripts': ['channel-tasks-admin=django_tasks.entrypoint:manage_channel_tasks']},
    install_requires=[
        'Django', 'django-filter', 'django-extensions', 'django-request-logging', 'adrf',
        'channels', 'channels-redis', 'tzdata', 'psycopg[pool]', 'websocket-client',
        'django-sass-compiler',
    ],
    extras_require={'dev': ['ipdb', 'ipython'],
                    'mypy': ['mypy', 'django-stubs', 'djangorestframework-stubs[compatible-mypy]',
                             'types-beautifulsoup4', 'types-setuptools'],
                    'test': [
                        'pytest', 'pytest-cov', 'pytest-django', 'pytest-asyncio', 'pytest-timeout',
                        'bdd-coder==2.2.3.dev3', 'beautifulsoup4']},
)
