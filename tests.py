import os
import shlex
import subprocess

import pytest


VERSION = '2.13'
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
VIRTUALENV_DIR = os.environ['VIRTUAL_ENV']
INSTALL_COMMAND_BASE = 'pip install --egg {0} '.format(PROJECT_DIR)


VERSIONS = {
    '2.10': (
        '4fecc99b066cb1a346035bf022607104',
        '058cd8b7b4b9688507701b5e648fd821',
        'fd0dafc3ada3619edda2961f2beadc5c',
        '082e91e5c8994a7879710caeed62e334'
    ),
    '2.11': (
        'bf0d731cd34fd07e22f4641c9aec8483',
        '7a7336caea140f6ac1cb8fae8df50d36',
        '447ebc91ac355fc11e960c95f2c15622',
        '44443738344b887ff1fe94710a8d45dc'
    )
}


@pytest.fixture(params=VERSIONS)
def version_info(request):
    return request.param


class Base(object):
    def _uninstall(self):
        try:
            subprocess.check_call(shlex.split('pip uninstall chromedriver_installer -y'))
        except subprocess.CalledProcessError:
            pass

        chromedriver_executable = os.path.join(VIRTUALENV_DIR,
                                               'bin', 'chromedriver')

        if os.path.exists(chromedriver_executable):
            print('REMOVING chromedriver executable: ' + chromedriver_executable)
            os.remove(chromedriver_executable)

    def teardown(self):
        self._uninstall()

    def _not_available(self):
        with pytest.raises(OSError):
            subprocess.check_call(shlex.split('chromedriver --version'))


class TestFailure(Base):
    def test_bad_checksum(self):
        self._not_available()

        command = INSTALL_COMMAND_BASE + (
            '--install-option="--chromedriver-version=2.10" '
            '--install-option="--chromedriver-checksums=foo,bar,baz"'
        )

        error_message = subprocess.Popen(
            shlex.split(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).communicate()[0]

        assert 'failed with error code 1' in str(error_message)


class VersionBase(Base):

    def test_version(self, version_info):
        self.version = version_info
        self.checksums = VERSIONS[version_info]

        # Chromedriver executable should not be available.
        self._not_available()

        subprocess.check_call(shlex.split(self._get_install_command()))

        # ...the chromedriver executable should be available...
        expected_version = subprocess.Popen(
            shlex.split('chromedriver -v'),
            stdout=subprocess.PIPE
        ).communicate()[0]

        # ...and should be of the right version.
        assert self.version in str(expected_version)


class TestVersionOnly(VersionBase):
    def _get_install_command(self):
        return INSTALL_COMMAND_BASE + \
               '--install-option="--chromedriver-version={0}"'.format(self.version)


class TestVersionAndChecksums(VersionBase):
    def _get_install_command(self):
        return INSTALL_COMMAND_BASE + (
            '--install-option="--chromedriver-version={0}" '
            '--install-option="--chromedriver-checksums={1}"'
        ).format(self.version, ','.join(self.checksums))
