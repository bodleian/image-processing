# Introduction

Image-processing is a Python library that converts a source image (TIFF or JPEG) to a JP2 file with a focus on digital preservation and making sure the conversion is reversible.

At the Bodleian we use it to generate the derivative files we ingest into Digital Bodleian for display and preservation.


### Use cases
- An all-in-one workflow to go from source file to derivatives including all validation checks. The defaults are tailored to Digital Bodleian preferences, but this is customisable.
- Individual functions to be called separately from a workflow manager like Goobi.
- Easy TIFF to JP2 conversion from Python: basic Python wrapper around Kakadu, along with some tested parameter recipes.


## Quick start

Install image-processing

To run a full conversion on a TIFF file, with validation, format checks, XMP extraction and creation of a thumbnail JPEG:

```python
from image_processing.derivative_files_generator import DerivativeFilesGenerator
derivatives_gen = DerivativeFilesGenerator(kakadu_base_path="/opt/kakadu")
derivatives_gen.generate_derivatives_from_tiff(tiff_filepath, output_folder)
```

To access the validation and conversion functions separately so they can be integrated into a workflow system like Goobi:

```python
from image_processing.derivative_files_generator import DerivativeFilesGenerator
from image_processing import kakadu, validation
derivatives_gen = DerivativeFilesGenerator(kakadu_base_path="/opt/kakadu", 
                                           kakadu_compress_options=kakadu.DEFAULT_LOSSLESS_COMPRESS_OPTIONS)

# each of these statements can be run separately, with different instances of DerivativeFilesGenerator
validation.check_image_suitable_for_jp2_conversion(tiff_filepath)
derivatives_gen.generate_jp2_from_tiff(tiff_filepath, jp2_filepath)
derivatives_gen.validate_jp2_conversion(tiff_filepath, jp2_filepath, check_lossless=True)
```

To just use Kakadu directly through the wrapper:
```python
from image_processing import kakadu
kdu = kakadu.Kakadu(kakadu_base_path="/opt/kakadu")
kdu.kdu_compress(tiff_file, jp2_filepath, kakadu_options=kakadu.DEFAULT_LOSSLESS_COMPRESS_OPTIONS)
```


## Digital Preservation

This package has a strong focus on digital preservation, as we want to use lossless JP2s as our preservation master files. It was developed with input from our digital preservation team

By default it checks:
- the JP2 is valid (using [jpylyzer](http://jpylyzer.openpreservation.org/))
- the JP2 can be converted back into a TIFF
- this TIFF has the same pixels as the source TIFF (or the TIFF we converted from the source JPEG)
- this TIFF has the same colour profile and mode as the source image

It doesn't check:
- the technical metadata is correctly copied over to the JP2 (but we do extract this to a separate file)
- the JP2 displays as expected in viewers
- the JPG to TIFF conversion, if the source file was a JPG (beyond checking the colour profiles match). It is a lossy conversion, so the pixels will not be identical

We have run tests on a wide sample of source images from our repository. We cannot share this test repository on GitHub due to copyright issues, but if you want to run your own tests these automatic lossless checks should simplify that. The full lossless checks can be disabled in production, but we'd recommend keeping them enabled if digital preservation is a concern.

Note: our testing has been focused on the source images we ingest, not all possible formats. The `validation.check_image_suitable_for_jp2_conversion` function is run when generating derivatives, and should fail for image formats we have not tested.

See [JPEG 2000 Colour Management](JP2_colour_management.md) for some more background information and recommendations.

## Installation

- Compatible with both Python 2.7 and 3
- Can be installed with `pip`

### Dependencies
- [Exempi](https://libopenraw.freedesktop.org/wiki/Exempi/)
- [Kakadu](http://kakadusoftware.com/)
    - should be compiled with libtiff support if you want to process compressed TIFFs.
    - modify the makefile `apps/make/Makefile-<OS>`. Add `-DKDU_INCLUDE_TIFF` to CFLAGS and add `-ltiff` to LIBS

### Pip dependencies

#### Pillow

Needs some image packages installed (may not need lcms2 depending on which TIFF formats you'll be processing)

`yum install lcms2 lcms2-devel libtiff libtiff-devel libjpeg libjpeg-devel`

The virtual environment python needs to match the Python.h used by GCC. If necessary, use `export C_INCLUDE_PATH=/usr/local/include/python2.7/`

#### Jypylyzer

Needs a relatively recent pip version to install - it fails on 1.4.
