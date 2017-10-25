# -*- coding: utf-8 -*-
"""
Taken from goobi project 6/4/2016. Same API
"""

import os.path, commands


class Exempi(object):
    """
        Using exempi to extract XMP information from image formats into an xml file.

        see http://libopenraw.freedesktop.org/wiki/Exempi/
    """

    def __init__(self, exempi_app, logger=None):

        self.exempi = exempi_app
        self.logger = logger

        self.transform = None

    def generate(self, image_file, output_file):

        """
            Create a new file from the XMP data within an image file.

            output_file 's folder must exist.
        """

        if not os.path.exists(self.exempi):
            self._error('Generating XSLT: Exempi tool not found at "' + self.exempi + '"')

            return False

        if not os.path.exists(image_file):
            self._error('Image file not found at "' + image_file + '"')

            return False

        command = self._default_command()
        command += '-o "' + output_file + '" '
        command += image_file

        print command

        returns = commands.getstatusoutput(command)

        print returns

        if returns[0] != 0:
            # There has been an error!
            self._error('Error executing exempi, using image="' + image_file + '". Output follows:\n------\n' + returns[
                1] + '\n------')

            return False

        return True

    def _default_command(self):
        command = self.exempi + " "
        command += '-x '  # output xml
        command += '-R '  # reconcile (I *believe* this removes duplicates)

        return command

    def _error(self, message):
        if self.logger:
            self.logger.error(self._wrap_message(message))
        print "Error:" + message

    def _warning(self, message):
        if self.logger:
            self.logger.warning(self._wrap_message(message))

    def _info(self, message):
        if self.logger:
            self.logger.info(self._wrap_message(message))

    def _debug(self, message):
        if self.logger:
            self.logger.debug(self._wrap_message(message))

    def _wrap_message(self, message):
        return "class Exempi() :: " + message
