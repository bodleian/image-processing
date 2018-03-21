from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import subprocess
import logging
from image_processing.exceptions import KakaduError
from image_processing import utils

DEFAULT_COMPRESS_OPTIONS = [
    'Clevels=6',
    'Clayers=6',
    'Cprecincts={256,256},{256,256},{128,128}',
    'Stiles={512,512}',
    'Corder=RPCL',
    'ORGgen_plt=yes',
    'ORGtparts=R',
    'Cblk={64,64}',
    'Cuse_sop=yes',
    'Cuse_eph=yes',
    '-flush_period', '1024']
"""Some default command line options for :func:`kdu_compress`, without lossy/lossless specified."""

LOSSLESS_OPTIONS = [
    "Creversible=yes",
    "-rate", "-"]
""":func:`kdu_compress` command line options which make the compression lossless"""

DEFAULT_LOSSLESS_COMPRESS_OPTIONS = DEFAULT_COMPRESS_OPTIONS + LOSSLESS_OPTIONS
"""Default lossless command line options for :func:`kdu_compress`"""

LOSSY_OPTIONS = ["-rate", '3']
""":func:`kdu_compress` command line options which make the compression lossy"""

ALPHA_OPTION = '-jp2_alpha'
""":func:`kdu_compress` command line option for images with alpha channels"""


class Kakadu(object):
    """
    Python wrapper for jp2 compression and expansion functions in Kakadu (http://kakadusoftware.com/)
    """

    def __init__(self, kakadu_base_path):
        """
        :param kakadu_base_path: The location of the kdu_compress and kdu_expand executables
        """
        self.kakadu_base_path = kakadu_base_path
        self.log = logging.getLogger(__name__)
        if not utils.cmd_is_executable(self._command_path('kdu_compress')):
            raise OSError("Could not find executable {0}. Check kakadu is installed and kdu_compress exists at the configured path"
                          .format(self._command_path('kdu_compress')))
        if not utils.cmd_is_executable(self._command_path('kdu_expand')):
            self.log.error("Could not find executable {0}. Lossless checks will not work. "
                           "Check kakadu is installed and kdu_expand exists at the configured path"
                          .format(self._command_path('kdu_expand')))

    def _command_path(self, command):
        return os.path.join(self.kakadu_base_path, command)

    def kdu_compress(self, input_filepaths, output_filepath, kakadu_options):
        """
        Converts an image file supported by kakadu to jpeg2000
        Bitonal or greyscale image files are converted to a single channel jpeg2000 file

        :param input_filepaths: Either a single filepath or a list of filepaths.
            If given three single channel files, Kakadu will combine them into a single 3 channel image
        :param output_filepath:
        :param kakadu_options: command line arguments
        """
        self.run_command('kdu_compress', input_filepaths, output_filepath, kakadu_options)

    def kdu_expand(self, input_filepath, output_filepath, kakadu_options):
        """
        Converts a jpeg2000 file to tif

        :param input_filepath:
        :param output_filepath:
        :param kakadu_options: command line arguments
        """
        self.run_command('kdu_expand', input_filepath, output_filepath, kakadu_options)

    def run_command(self, command, input_files, output_file, kakadu_options):
        if not isinstance(input_files, list):
            input_files = [input_files]

        # the -i parameter can have multiple files listed
        for input_file in input_files:
            if not os.access(input_file, os.R_OK):
                raise IOError("Could not access image file {0} to convert".format(input_file))

        if not os.access(os.path.dirname(output_file), os.W_OK):
            raise IOError("Could not write to output path {0}".format(output_file))

        input_option = ",".join(["{0}".format(item) for item in input_files])

        command_options = [self._command_path(command), '-i', input_option, '-o', output_file] + kakadu_options

        self.log.debug(' '.join(['"{0}"'.format(c) if ('{' in c or ' ' in c) else c for c in command_options]))

        try:
            subprocess.check_call(command_options, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise KakaduError('Kakadu {0} failed on {1}. Command: {2}, Error: {3}'.
                              format(command, input_option, ' '.join(command_options), e))
