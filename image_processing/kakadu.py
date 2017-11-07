import os
import subprocess
from exceptions import KakaduError

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
        if not os.access(self._kdu_compress_path(), os.X_OK):
            raise IOError("Couldn't execute kdu_compress at {0}".format(self._kdu_compress_path()))

    def _kdu_compress_path(self):
        return os.path.join(self.kakadu_base_path, 'kdu_compress')

    def kdu_compress(self, input_files, output_file, kakadu_options):
        if not isinstance(input_files, list):
            input_files = [input_files]

        # the -i parameter can have multiple files listed
        for input_file in input_files:
            if not os.access(input_file, os.R_OK):
                raise IOError("Couldn't access image file {0} to convert".format(input_file))

        if not os.access(os.path.dirname(output_file), os.W_OK):
            raise IOError("Couldn't write to output path {0}".format(output_file))

        input_option = ",".join(["{0}".format(item) for item in input_files])

        command_options = [self._kdu_compress_path(), '-i', input_option, '-o', output_file] + kakadu_options

        print ' '.join(command_options)
        try:
            subprocess.check_call(command_options, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise KakaduError('Kakadu conversion to jpeg2000 failed on {0}. Command: {1}'.
                              format(input_option, ' '.join(command_options)), e)
