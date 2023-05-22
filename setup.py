import setuptools


tests_require = ['pytest', 'pytest-cov', 'pytest-django', 'pytest-asyncio', 'bdd-coder==2.2.3.dev2']

setuptools.setup(
    name='mastermind',
    version='0.1',
    packages=setuptools.find_packages(),
    install_requires=[
        'Django', 'django-filter', 'django-sesame', 'djangorestframework', 'psycopg2-binary',
        'channels', 'channels-redis', 'daphne', 'tzdata'],
    extras_require={'dev': ['ipdb', 'ipython'],
                    'mypy': ['mypy', 'django-stubs', 'djangorestframework-stubs[compatible-mypy]'],
                    'test': tests_require},
    tests_require=tests_require
)
