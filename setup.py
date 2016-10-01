#
#  Got documentation from: http://peterdowns.com/posts/first-time-with-pypi.html
#
#   1. Create tag:
#       git tag 2.0.0 -m "Adds a tag so that we can put this new version on PyPI."
#
#   2. Push tag:
#       git push --tags origin master
#
#   3. Upload your package to PyPI Test:
#       python setup.py register -r pypitest
#       python setup.py sdist upload -r pypitest
#
#   4. Upload to PyPI Live
#       python setup.py register -r pypi
#       python setup.py sdist upload -r pypi
#

from distutils.core import setup
setup(
    name='siridb-connector',
    packages=['siridb-connector'],
    version='2.0.0',
    description='SiriDB Connector',
    author='Jeroen van der Heijden',
    author_email='jeroen@transceptor.technology',
    url='https://github.com/transceptor-technology/siridb-connector',
    download_url='https://github.com/transceptor-technology/siridb-connector/tarball/2.0.0',
    keywords=['siridb', 'connector', 'database', 'client'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Database',
        'Topic :: Software Development'
    ],
    install_requires=['qpack']
)
