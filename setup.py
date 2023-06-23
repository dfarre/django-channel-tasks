import setuptools


tests_require = ['pytest', 'pytest-cov', 'pytest-django', 'pytest-asyncio', 'beautifulsoup4',
                 'bdd-coder==2.2.3.dev2']

setuptools.setup(
    name='django-tasks',
    version='0.1',
    packages=setuptools.find_packages(),
    install_requires=[
        'Django', 'django-filter', 'django-extensions', 'djangorestframework',
        'channels', 'channels-redis', 'daphne', 'tzdata', 'psycopg2-binary'],
    extras_require={'dev': ['ipdb', 'ipython'],
                    'mypy': ['mypy', 'django-stubs', 'djangorestframework-stubs[compatible-mypy]'],
                    'test': tests_require},
    tests_require=tests_require
)
