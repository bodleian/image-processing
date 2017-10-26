import os
import subprocess

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


class KakaduError(Exception):
    pass


class Kakadu(object):

    def __init__(self, kakadu_base_path):
        self.kakadu_base_path = kakadu_base_path

    def _kdu_compress_path(self):
        return os.path.join(self.kakadu_base_path, 'kdu_compress')

    def kdu_compress(self, input, output, kakadu_options):
        command_options = [self._kdu_compress_path(),'-i', input, '-o', output] + kakadu_options

        # the -i parameter can have multiple files listed
        for input_filepath in input.split(','):
            if not os.access(input_filepath, os.R_OK):
                raise (IOError("Couldn't access image file {0} to convert".format(input_filepath)))

        if not os.access(os.path.dirname(output), os.W_OK):
            raise (IOError("Couldn't write to output path {0}".format(output)))
        print ' '.join(command_options)
        try:
            subprocess.check_call(command_options, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise(KakaduError('Kakadu conversion to jpeg2000 failed on {0}. Command: {1}'.
                              format(input, ' '.join(command_options)), e))


def test():
    lossless = DEFAULT_BDLSS_OPTIONS + ["Creversible=yes", "-rate", "-"]
    lossy = DEFAULT_BDLSS_OPTIONS+ ["-rate", "3"]
    monochrome = DEFAULT_BDLSS_OPTIONS+ ["-no_palette"]
