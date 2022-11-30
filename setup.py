"""
Upload to PyPI

python setup.py sdist
twine upload --repository pypitest dist/siridb-connector-X.X.X.tar.gz
twine upload --repository pypi dist/siridb-connector-X.X.X.tar.gz

locan installation: pip install -e .
"""

from distutils.core import setup
import setuptools
from siridb import __version__


VERSION = __version__


with open('README.md', 'r') as f:
    long_description = f.read()


setup(
    name='siridb-connector',
    packages=[
        'siridb',
        'siridb.connector',
        'siridb.connector.lib'],
    version=VERSION,
    description='SiriDB Connector',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Jeroen van der Heijden',
    author_email='jeroen@cesbit.com',
    url='https://github.com/SiriDB/siridb-connector',
    download_url='https://github.com/SiriDB/'
                 'siridb-connector/tarball/{}'.format(VERSION),
    keywords=['siridb', 'connector', 'database', 'client'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Database',
        'Topic :: Software Development'
    ],
    install_requires=['qpack']
)
