from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os, re
import subprocess
import logging
from image_processing.exceptions import ImageMagickError


class ImageMagick(object):
    def __init__(self, image_magick_location):
        self.image_magick_location = image_magick_location
        self.log = logging.getLogger(__name__)

    def _command_location(self, command):
        return os.path.join(self.image_magick_location, command)

    def _check_input_file_readable(self, input_file):
        # may specify image sequence
        actual_input_filepath = re.sub(r'\[\d+\]$', '', input_file)
        if not os.access(actual_input_filepath, os.R_OK):
            raise IOError("Couldn't read input file {0}".format(actual_input_filepath))

    def convert(self, input_file, output_file, initial_options=None, post_options=None):
        """
        :param input_file:
        :param output_file:
        :param initial_options: command line arguments which need to go before the input file
        :param post_options: command line arguments which need to go after the input file
        :return:
        """
        self._check_input_file_readable(input_file)

        if not os.access(os.path.dirname(output_file), os.W_OK):
            raise IOError("Couldn't write to output path {0}".format(output_file))

        self.run_command('convert', input_file, output_file, initial_options=initial_options, post_options=post_options)

    def mogrify(self, input_file, initial_options=None, post_options=None):
        """
        IMPORTANT: if changing formats, and the input_file extension differs from the format extension,
        the created file will have the format extension
        :param input_file:
        :param initial_options: command line arguments which need to go before the input file
        :param post_options: command line arguments which need to go after the input file
        :return:
        """
        self._check_input_file_readable(input_file)

        self.run_command('mogrify', input_file, initial_options=initial_options, post_options=post_options)

    def run_command(self, command, input_file, output_file=None, initial_options=None, post_options=None):
        """
        :param input_file:
        :param output_file:
        :param initial_options: command line arguments which need to go before the input file
        :param post_options: command line arguments which need to go after the input file
        :return:
        """
        if initial_options is None:
            initial_options = []
        if post_options is None:
            post_options = []

        command_options = [self._command_location(command)] + initial_options + [input_file] + post_options
        if output_file:
            command_options += [output_file]

        self.log.debug(' '.join(command_options))
        try:
            subprocess.check_call(command_options, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise ImageMagickError('Image magick command {0} failed: {1}'.
                                   format(' '.join(command_options), e.message))
