from setuptools import setup, find_packages
import os
import uwsgi_it_api

CLASSIFIERS = [
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

setup(
    author="Unbit sas",
    author_email="info@unbit.com",
    name='uwsgi_it_api',
    version=uwsgi_it_api.__version__,
    description='uwsgi.it api',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    url="https://github.com/unbit/uwsgi.it",
    license='MIT License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    install_requires=[
        'django',
        'south',
        'ipaddress',
        'psycopg2',
        'dnspython',
        'pycrypto',
        'pylibmc',
    ],
    packages=find_packages(exclude=["example", "example.*"]),
    include_package_data=True,
    zip_safe = False,
)
