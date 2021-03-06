import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
    'PasteScript',
    'plaster_pastedeploy',
    'pyramid',
    'pyramid_chameleon',
    'pyramid_debugtoolbar',
    'waitress',
    'python-gammu',
    'colander',
    'deform',
    'phonenumbers',
]

tests_require = [
    'WebTest >= 1.3.1',  # py3 compat
    'pytest >= 3.7.4',
    'pytest-cov',
]

setup(
    name='semes',
    version='0.3',
    description='semes',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    author='Nestor Diaz',
    author_email='nestor@tiendalinux.com',
    url='https://github.com/nesiax/semes',
    keywords='web pyramid pylons sms gammu',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'testing': tests_require,
    },
    install_requires=requires,
    entry_points={
        'paste.app_factory': [
            'main = semes:main',
        ],
    },
)
