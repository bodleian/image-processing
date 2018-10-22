Image Processing
================
.. inclusion-marker-intro-start

Image-processing is a Python library that converts a source image (TIFF or JPEG) to a JP2 file with a focus on digital preservation and making sure the conversion is reversible.

At the Bodleian we use it to generate the derivative image files we ingest into Digital Bodleian for both delivery and long-term preservation.


.. image:: https://travis-ci.org/bodleian/image-processing.svg?branch=master
    :target: https://travis-ci.org/bodleian/image-processing
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

- Compatible with both Python 2.7 and 3.5+

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


.. inclusion-marker-intro-end

More information
----------------

See our `documentation <https://image-processing.readthedocs.io/>`__. If your question isn't covered there, please `submit an issue <https://github.com/bodleian/image-processing/issues>`_ or `contact us <mailto:mel.mason@bodleian.ox.ac.uk>`_.
