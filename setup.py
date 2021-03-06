import os
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


def package_data(pkg, roots):
    """Generic function to find package_data.

    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.

    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


class Tox(TestCommand):
    user_options = [('tox-args=', 'a', 'Arguments to pass to tox')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import tox
        import shlex
        args = self.tox_args
        if args:
            args = shlex.split(self.tox_args)
        errno = tox.cmdline(args=args)
        sys.exit(errno)

setup(
    name="xblock-adaptive-numeric-input",
    version="0.0.1",
    description="Enables instructors to add numeric input problems with '\
        adaptive feedback.",
    license='AGPL-3.0',
    packages=[
        'adaptivenumericinput',
    ],
    install_requires=[
        'django',
        'django_nose',
        'mock',
        'coverage',
        'mako',
        'XBlock',
        'xblock-utils',
        'enum34',
    ],
    dependency_links=[
        'https://github.com/edx/xblock-utils/tarball/'
        'c39bf653e4f27fb3798662ef64cde99f57603f79#egg=xblock-utils',
    ],
    entry_points={
        'xblock.v1': [
            'adaptivenumericinput = adaptivenumericinput:AdaptiveNumericInput',
        ],
    },
    package_dir={
        'adaptivenumericinput': 'adaptivenumericinput',
    },
    package_data=package_data('adaptivenumericinput', ['static', 'public']),
    classifiers=[
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: JavaScript',
        'Programming Language :: Python',
        'Topic :: Education',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
