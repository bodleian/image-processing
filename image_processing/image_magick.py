from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import subprocess
import logging
from image_processing.exceptions import ImageMagickError


class ImageMagick(object):
    def __init__(self, image_magick_location=""):
        self.image_magick_location = image_magick_location
        if not os.access(self._command_location('convert'), os.X_OK):
            raise IOError("Couldn't execute image magick convert at {0}".format(image_magick_location))

    def _command_location(self, command):
        return os.path.join(self.image_magick_location, command)

    def convert(self, input_file, output_file, initial_options=None, post_options=None):
        """
        :param input_file:
        :param output_file:
        :param inital_options: command line arguments which need to go before the input file
        :param post_options: command line arguments which need to go after the input file
        :return:
        """
        if initial_options is None:
            initial_options = []
        if post_options is None:
            post_options = []

        if not os.access(input_file, os.R_OK):
            raise IOError("Couldn't read input file {0}".format(input_file))

        if not os.access(os.path.dirname(output_file), os.W_OK):
            raise IOError("Couldn't write to output path {0}".format(output_file))

        command_options = [self._command_location('convert')] + initial_options + [input_file] + post_options + [output_file]

        logging.debug(' '.join(command_options))
        try:
            subprocess.check_call(command_options, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise ImageMagickError('Image magick convert command failed: {0}'.
                                   format(' '.join(command_options)), e)
