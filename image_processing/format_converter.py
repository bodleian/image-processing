
import os
import subprocess
from PIL import Image
from kakadu import DEFAULT_BDLSS_OPTIONS, LOSSLESS_OPTIONS, Kakadu

class ImageProcessingError(Exception):
    pass

#todo: make configurable
KAKADU_BASE_PATH= '/opt/kakadu'

def convert_unsupported_file_to_jpeg2000(input_filepath, output_filepath, strip_metadata=False):
    """
    Converts an image file unsupported by kakadu (e.g. jpg) losslessly to jpeg2000 by converting it to tiff first
    :param strip_metadata: True if you want to remove the metadata during the conversion process.
    Useful for images with badly formed metadata that wouldn't otherwise pass jp2 validation
    """
    tiff_filepath = os.path.splitext(output_filepath)[0] + '.tif'
    convert_to_tiff(input_filepath, tiff_filepath, strip_metadata=strip_metadata)
    convert_to_jpeg2000(tiff_filepath, output_filepath)
    os.remove(tiff_filepath)


def convert_to_jpeg2000(input_filepath, output_filepath, lossless=True):
    """
    Converts an image file supported by kakadu losslessly to jpeg2000
    """

    if lossless:
        extra_options = LOSSLESS_OPTIONS
    else:
        extra_options = ["-rate", "3"]

    kakadu_options = DEFAULT_BDLSS_OPTIONS + extra_options
    kakadu = Kakadu(KAKADU_BASE_PATH)
    kakadu.kdu_compress(input_filepath, output_filepath, kakadu_options)


def repage_image(input_filepath, output_filepath):
    """Fix negative image positions unsupported problems"""
    if not os.access(os.path.dirname(input_filepath), os.R_OK):
        raise(ImageProcessingError("Couldn't read from input path {0}".format(input_filepath)))
    if not os.access(os.path.dirname(output_filepath), os.W_OK):
        raise(ImageProcessingError("Couldn't write to output path {0}".format(output_filepath)))
    action = 'convert "{0}" +repage "{1}"'.format(input_filepath, output_filepath)

    success = _run_trusted_shell_action(action)

    if not success:
        raise ImageProcessingError('repage image conversion failed on {0}'.format(input_filepath))

def is_monochrome(input_filepath):
    if not os.access(input_filepath, os.R_OK):
        raise(ImageProcessingError("Couldn't access image file {0} to test".format(input_filepath)))
    try:
        image_mode = get_colourspace(input_filepath)  # colour mode of image
        if image_mode == 'L':  # greyscale
            return True
        elif image_mode == '1':  # Bitonal
            return True
        elif image_mode == 'RGB':  # RGB colour
            return False
        elif image_mode == 'RGBA':  # RGBA colour
            return False
        elif image_mode == 'sRGB':  # sRGB colour
            return False
        else:
            print "Could not identify image colour mode.\n"
            raise(ImageProcessingError("Could not identify image colour mode of "+ input_filepath))
    except Exception as e:
        raise(ImageProcessingError("PIL failed to open {0}: {1}".format(input_filepath,e)))


def get_colourspace(image_file):
    # get properties of image
    try:
        #todo: consider removing PIL entirely. First need to make sure the imagemagick monotone colour space results are the same.
        colourspace = Image.open(image_file).mode  # colour mode of image
        return colourspace
    except IOError as e:
        # if PIP won't support the file, try imagemagick
        print "PIP doesn't support {0}: {1}. Trying image magick".format(image_file, e)
        colourspace = subprocess.check_output("identify -format %[colorspace] '{0}'".format(image_file),
                                              shell=True).rstrip()
        return colourspace


def convert_monochrome_to_lossless_jpeg2000(input_filepath, output_filepath):
    """
    Converts an bitonal or greyscale image file supported by kakadu losslessly to jpeg2000
    """
    kakadu_options = DEFAULT_BDLSS_OPTIONS + LOSSLESS_OPTIONS + ["-no_palette"]
    kakadu = Kakadu(KAKADU_BASE_PATH)
    kakadu.kdu_compress("'{0}','{0}','{0}'".format(input_filepath), output_filepath, kakadu_options)


def convert_to_tiff(input_filepath, output_filepath, strip_metadata=False):
    """
    Converts the file to tiff format
    """
    # image magick is currently faster on my machine, so I'm using that but the library used can be changed here
    # Note graphicsmagick strips out image metadata by default, so should be avoided unless we put in a workaround
    return convert_to_tiff_with_library_choice(input_filepath, output_filepath, use_graphics_magick=False,strip_metadata=strip_metadata )

def convert_to_tiff_with_library_choice(input_filepath, output_filepath, use_graphics_magick, strip_metadata=False):
    return convert_to_format_with_library_choice(input_filepath, output_filepath,format='tif', use_graphics_magick=use_graphics_magick,strip_metadata=strip_metadata )

def convert_tiff_colour_depth(input_filepath, output_filepath):
    if not os.access(input_filepath, os.R_OK):
        raise (ImageProcessingError("Couldn't access image file {0} to convert".format(input_filepath)))

    if not os.access(os.path.dirname(output_filepath), os.W_OK):
        raise (ImageProcessingError("Couldn't write to output path {0}".format(output_filepath)))

    action = "convert '{0}' -compress none -depth 8 -type truecolor -alpha off '{1}'".format(input_filepath,output_filepath)
    success = _run_trusted_shell_action(action)

    if not success:
        raise ImageProcessingError('Tiff conversion to 8 bit colour depth failed on {0}'.format(input_filepath))


def mogrify_tiff_colour_profile(input_filepath):
    if not os.access(input_filepath, os.W_OK):
        raise (ImageProcessingError("Couldn't write to image file {0} to convert".format(input_filepath)))

    action = "mogrify -profile /opt/kakadu/sRGB_v4_ICC_preference.icc -compress none -depth 8 -type truecolor -alpha off '{0}'".format(input_filepath)
    success = _run_trusted_shell_action(action)

    if not success:
        raise ImageProcessingError('Tiff conversion to sRGB failed on {0}'.format(input_filepath))

def convert_tiff_colour_profile(input_filepath, output_filepath, input_is_monochrome=False):
    if not os.access(input_filepath, os.R_OK):
        raise (ImageProcessingError("Couldn't access image file {0} to convert".format(input_filepath)))
    if not os.access(os.path.dirname(output_filepath), os.W_OK):
        raise (ImageProcessingError("Couldn't write to output path {0}".format(output_filepath)))

    options = '-profile /opt/kakadu/sRGB_v4_ICC_preference.icc'
    if input_is_monochrome:
        options += ' -compress none -depth 8 -type truecolor -alpha off'
    action = "convert {0} '{1}' '{2}'".format(options, input_filepath,output_filepath)
    success = _run_trusted_shell_action(action)

    if not success:
        raise ImageProcessingError('Tiff conversion to sRGB failed on {0}'.format(input_filepath))


def convert_to_format_with_library_choice(input_filepath, output_filepath, format, use_graphics_magick=False, strip_metadata=False):
    """
    Uses image magick or graphics magick to convert the file to the given format
    """

    if not os.access(input_filepath, os.R_OK):
        raise(ImageProcessingError("Couldn't access image file {0} to convert".format(input_filepath)))

    if not os.access(os.path.dirname(output_filepath), os.W_OK):
        raise(ImageProcessingError("Couldn't write to output path {0}".format(output_filepath)))

    action = "convert -format {0} {1} '{2}[0]' '{3}'".format(format,"-strip" if strip_metadata else "", input_filepath, output_filepath)
    if use_graphics_magick:
        action = "gm " + action

    success = _run_trusted_shell_action(action)

    if not success:
        raise ImageProcessingError('Conversion to {0} failed on {1}'.format(format, input_filepath))



def _run_trusted_shell_action(action):
    proc = subprocess.Popen(action, shell=True, stdout=subprocess.PIPE, close_fds=True)
    proc.wait()

    if proc.returncode != 0:
        print('failed with return code: {0}'.format(proc.returncode))
        return False
    return True