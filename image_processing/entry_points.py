import argparse
import os

from image_processing.conversion import Converter
from image_processing.derivative_files_generator import DerivativeFilesGenerator


def generate_derivatives_from_tiff():
    """
    A basic command line script that runs :func:`~image_processing.derivative_files_generator.DerivativeFilesGenerator.generate_derivatives_from_tiff`"
    """
    parser = argparse.ArgumentParser(description="Generate a JP2 from a TIFF, and check the conversion is lossless. "
                                                 "Also generates a thumbnail and records for digital preservation")
    parser.add_argument('tiff_filepath', help='Tiff to convert')
    parser.add_argument('-o', '--output_folder', help='Folder to create derivatives in', required=False, default=None)
    parser.add_argument('-k', '--kakadu_path', help='Base path to kakadu executables', required=False, default='/opt/kakadu')
    args = parser.parse_args()
    output_folder = args.output_folder
    if not output_folder:
        output_folder, _ = os.path.splitext(os.path.basename(args.tiff_filepath))
    output_folder = os.path.abspath(output_folder)
    generator = DerivativeFilesGenerator(require_icc_profile_for_colour=False,
                                         require_icc_profile_for_greyscale=False,
                                         use_default_filenames=False,
                                         kakadu_base_path=args.kakadu_path)
    generator.generate_derivatives_from_tiff(args.tiff_filepath, output_folder, include_tiff=False, save_jpylyzer_output=True)
    print('Files created at {0}'.format(output_folder))


def convert_icc_profile():
    """
    A basic command line script that runs :func:`~image_processing.conversion.Converter.convert_icc_profile`"
    """
    parser = argparse.ArgumentParser(description="Converts the icc profile of a file")
    parser.add_argument('image_filepath', help='Tiff to convert')
    parser.add_argument('output_image_filepath', help='Output image path')
    parser.add_argument('-i', '--icc_filepath', help='Path to an icc profile', required=True)
    parser.add_argument('-c', '--colour_mode', help='New colour mode, if any', default=None, required=False)
    args = parser.parse_args()
    converter = Converter()
    converter.convert_icc_profile(args.image_filepath, args.output_image_filepath,
                                  icc_profile_filepath=args.icc_filepath, new_colour_mode=args.colour_mode)
    print('File created at {0}'.format(args.output_image_filepath))
