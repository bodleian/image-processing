Image Processing
================
.. inclusion-marker-intro-start

Image-processing is a Python library that converts a source image (TIFF or JPEG) to a JP2 file with a focus on digital preservation and making sure the conversion is reversible.

At the Bodleian we use it to generate the derivative image files we ingest into Digital Bodleian for both delivery and long-term preservation.

.. image:: https://github.com/bodleian/image-processing/actions/workflows/test-build.yml/badge.svg
    :target: https://github.com/bodleian/image-processing/actions/workflows/test-build.yml
    :alt: Build Status
.. image:: https://readthedocs.org/projects/image-processing/badge/?version=latest
    :target: https://image-processing.readthedocs.io/?badge=latest
    :alt: Documentation Status

Use cases
---------
- An all-in-one workflow to go from source file to derivatives including all validation checks. The defaults are tailored to Digital Bodleian preferences, but this is customisable.
- Individual functions to be called separately from a workflow manager like Goobi.
- Easy TIFF to JP2 conversion from Python: basic Python wrapper around Kakadu, along with some tested parameter recipes.


Installation
------------

``pip install git+https://github.com/bodleian/image-processing.git``

- Mostly tested on Python 3.8, but should also work on newer 3.x versions

Dependencies
~~~~~~~~~~~~
- `Exiftool`_
    - ``yum install perl-Image-ExifTool``
    - ``apt install exiftool``
- `Kakadu`_
    - If you want to process compressed TIFFs, compile it with libtiff support. In the makefile ``apps/make/Makefile-<OS>``, add ``-DKDU_INCLUDE_TIFF`` to CFLAGS and ``-ltiff`` to LIBS
- `Pillow`_ prerequisites before pip install
    - May need some image packages installed before pip installation (may not need lcms2 depending on which TIFF formats you'll be processing)
    - ``yum install lcms2 lcms2-devel libtiff libtiff-devel libjpeg libjpeg-devel``
        - If Pillow raises "decoder jpeg2k not available" errors while running the unit tests, try installing `openjpeg2`. This should only affect the unit tests, not normal running
        - You may need to delete and recreate the Python virtual environment for Pillow to properly link to these packages
    - The virtual environment's python binary needs to match the Python.h used by GCC. If necessary, use ``export C_INCLUDE_PATH=/usr/local/include/python2.7/``
- `Jpylyzer`_ prerequisites before pip install
    - Needs a relatively recent pip version to install - it fails on 1.4.

.. _Exiftool: http://owl.phy.queensu.ca/~phil/exiftool/
.. _Kakadu: http://kakadusoftware.com/
.. _Pillow: http://pillow.readthedocs.io/en/latest/
.. _Jpylyzer: http://jpylyzer.openpreservation.org/



Quick start
-----------

To run a full conversion on a TIFF file, with validation, format checks, XMP extraction and creation of a thumbnail JPEG:

From the command line:
::

    convert_tiff_to_jp2 input.tif

In Python:
::

    from image_processing.derivative_files_generator import DerivativeFilesGenerator
    derivatives_gen = DerivativeFilesGenerator(kakadu_base_path="/opt/kakadu")
    derivatives_gen.generate_derivatives_from_tiff("input.tif", "output/folder")


To access the validation and conversion functions separately so they can be integrated into a workflow system like Goobi:
::

    from image_processing.derivative_files_generator import DerivativeFilesGenerator
    from image_processing import kakadu, validation
    derivatives_gen = DerivativeFilesGenerator(kakadu_base_path="/opt/kakadu",
                                               kakadu_compress_options=kakadu.DEFAULT_LOSSLESS_COMPRESS_OPTIONS)

    # each of these statements can be run separately, with different instances of DerivativeFilesGenerator
    validation.check_image_suitable_for_jp2_conversion("input.tif")
    derivatives_gen.generate_jp2_from_tiff("input.tif", "output.jp2")
    derivatives_gen.validate_jp2_conversion("input.tif", "output.jp2", check_lossless=True)

To just use Kakadu directly through the wrapper:
::

    from image_processing import kakadu
    kdu = kakadu.Kakadu(kakadu_base_path="/opt/kakadu")
    kdu.kdu_compress("input.tif", "output.jp2", kakadu_options=kakadu.DEFAULT_LOSSLESS_COMPRESS_OPTIONS)


Development and Testing
-----------------------

We run a subset of our unit tests on Python versions 3.8+ using Github Actions. Tests that require Kakadu are skipped, as we cannot access the proprietary Kakadu executables from a public repository. Any changes should be tested locally, with Kakadu installed, rather than relying on the CI testing alone. You can use requirements.txt to set up a Python virtual environment.

The tests compare directly against image files to check for regression. When updating dependencies like Pillow these test image files may sometimes no longer match, especially jpgs. The current set of test images were generated with Pillow 10.0.1, Exiftool 12.40, and Kakadu 8.2


.. inclusion-marker-intro-end

More information
----------------

See our `documentation <https://image-processing.readthedocs.io/>`__. If your question isn't covered there, please `submit an issue <https://github.com/bodleian/image-processing/issues>`_ or `contact us <mailto:mel.mason@bodleian.ox.ac.uk>`_.
