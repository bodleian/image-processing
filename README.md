# Image processing

Library for common image processing tasks to avoid duplication of code.

Used for converting source images (tiff or jpg) to the derivative files we ingest into our repository - i.e. jp2s, xmp files and jpgs

## Dependencies
- Image Magick
- Exempi
- Kakadu
    - should be compiled with libtiff support if you want to process compressed tiffs.
    - modify the makefile `apps/make/Makefile-<OS>`. Add `-DKDU_INCLUDE_TIFF` to CFLAGS and add `-ltiff` to LIBS

### Pip dependencies

#### Pillow

Needs some image packages installed (may not need lcms2 if you won't be processing images using it)

`yum install lcms2 ylcms-devel libtiff libtiff-devel libjpeg libjpeg-devel`

The virtual environment python needs to match the Python.h used by gcc. If need be, use `export C_INCLUDE_PATH=/usr/local/include/python2.7/`

#### Jypylyzer

Needs a relatively recent pip version to install - it fails on 1.4.

## Used by
- [talbot-image-ingest](https://gitlab.bodleian.ox.ac.uk/digital.bodleian/talbot-image-ingest)
- [goobi/bdlss](https://gitlab.bodleian.ox.ac.uk/goobi/bdlss) (still in progress)