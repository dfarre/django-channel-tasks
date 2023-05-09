import setuptools


tests_require = ['pytest', 'pytest-cov', 'pytest-django', 'bdd-coder==2.2.3.dev1']

setuptools.setup(
    name='mastermind',
    version='0.1',
    packages=setuptools.find_packages(),
    install_requires=['Django', 'django-filter', 'djangorestframework', 'psycopg2-binary',
                      'channels', 'daphne', 'tzdata'],
    extras_require={'dev': ['ipdb', 'ipython'], 'test': tests_require},
    tests_require=tests_require
)
