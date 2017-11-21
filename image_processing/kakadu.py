from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import subprocess
import logging
from image_processing.exceptions import KakaduError

DEFAULT_BDLSS_OPTIONS = [
    '-jp2_space', 'sRGB',
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

LOSSLESS_OPTIONS = [
    "Creversible=yes",
    "-rate", "-"]


class Kakadu(object):

    def __init__(self, kakadu_base_path):
        self.kakadu_base_path = kakadu_base_path
        self.log = logging.getLogger(__name__)

    def _command_path(self, command):
        return os.path.join(self.kakadu_base_path, command)

    def kdu_compress(self, input_files, output_file, kakadu_options):
        self.run_command('kdu_compress', input_files, output_file, kakadu_options)

    def kdu_expand(self, input_files, output_file, kakadu_options):
        self.run_command('kdu_expand', input_files, output_file, kakadu_options)

    def run_command(self, command, input_files, output_file, kakadu_options):
        if not isinstance(input_files, list):
            input_files = [input_files]

        # the -i parameter can have multiple files listed
        for input_file in input_files:
            if not os.access(input_file, os.R_OK):
                raise IOError("Couldn't access image file {0} to convert".format(input_file))

        if not os.access(os.path.dirname(output_file), os.W_OK):
            raise IOError("Couldn't write to output path {0}".format(output_file))

        input_option = ",".join(["{0}".format(item) for item in input_files])

        command_options = [self._command_path(command), '-i', input_option, '-o', output_file] + kakadu_options

        self.log.debug(' '.join(command_options))
        try:
            subprocess.check_call(command_options, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise KakaduError('Kakadu {0} failed on {1}. Command: {2}, Error: {3}'.
                              format(command, input_option, ' '.join(command_options), e.message))