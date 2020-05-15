import os
import sys
from glob import glob
from distutils.core import setup
from distutils.cmd import Command


requirements = [
    "ciphercommon==2.0.13",
    "pyyaml>=5.1"
]

setup_requirements = [
    "setuptools"
]

test_requirements = [
    "pytest",
    "pytest-cov",
] + requirements


def get_version():
    """Load the version from __version__.py, without importing it."""
    global __version__
    try:
        with open("processinsights/__version__.py", "r") as f_v:
            exec("; ".join(["global __version__"] + [v.strip() for v in f_v.readlines()]), globals(), locals())
            return __version__
    except IOError:
        return "0.0.0"


__version__ = None
VERSION = get_version()
buildnumber = os.getenv('BUILD_BUILDNUMBER')


class CleanCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import shutil
        CLEAN_FILES = ["./**/*.pyc", "**/__pycache__","**/.pytest_cache",'.html', '.csv']
        for clean_file in CLEAN_FILES:
            paths = glob(os.path.normpath(os.path.join(os.getcwd(), clean_file)), recursive=True)
            for path in paths:
                path = str(path)
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)


class CheckVersionCommand(Command):
    """Outputs version checks to the build pipeline log."""

    user_options = []
    description = "Outputs version checks to the build pipeline log."

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        import pkg_resources
        if buildnumber is not None:
            git_label = subprocess.check_output(["git", "describe", "--tags", "--always"]).decode('utf-8')

            # this check prevents the build number from getting updated multiple times during a build pipeline
            if "-" not in buildnumber:
                print("##vso[build.updatebuildnumber]" + VERSION + "-" + buildnumber)

            old_version = pkg_resources.parse_version(git_label.split('-')[0])
            new_version = pkg_resources.parse_version(VERSION.split('-')[0])

            if new_version <= old_version:
                print("##vso[task.logissue type=error;] version number was not incremented from " + VERSION)
                print("##vso[task.logissue type=error;] version number was not incremented from " + VERSION, file=sys.stderr)
        else:
            print("##vso[build.updatebuildnumber]" + VERSION)


if __name__ == '__main__':
    setup(
        name="processinsights",
        description="ProcessInsights",
        keywords="",
        version=VERSION,
        cmdclass={'clean': CleanCommand, 'check_version': CheckVersionCommand},
        command_options={
            'clean': {}
        }
    )
