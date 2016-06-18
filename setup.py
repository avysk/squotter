"""Setup.py for setuptools."""

from setuptools import find_packages, setup
# from pip.req import parse_requirements
# REQS = [str(req.req) for req
#         in parse_requirements('requirements.txt', session=False)]
# No need to require anything, as we don't take in the tests
REQS = []
PKGS = find_packages(exclude=['tests'])
setup(
    name='squotter',
    version='0.0.1',
    packages=PKGS,
    install_requires=REQS,
    url='https://github.com/avysk/squotter',
    license='BSD 2-clause',
    author='Alexey Vyskubov',
    author_email='alexey@hotmail.fi',
    description='Tool to keep a collection of quotes as gopher directory.'
)
