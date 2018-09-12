Digital Preservation
====================

This package has a strong emphasis on digital preservation, as we want to use lossless JP2s as our preservation master files. It was developed with input from our `digital preservation team <http://www.dpoc.ac.uk>`_.

By default it checks:

- the JP2 is valid (using `jpylyzer`_)
- the JP2 can be converted back into a TIFF, which
    - has the same pixels as the source TIFF (or the TIFF we converted from the source JPEG)
    - has the same colour profile and mode as the source image

.. _Jpylyzer: http://jpylyzer.openpreservation.org/

It does not check:

- the technical metadata is correctly copied over to the JP2 (we extract this to a separate file)
- the JP2 displays as expected in viewers
- JPEG to TIFF conversion, if the source file was a JPEG (beyond checking the colour profiles match). This is a lossy conversion, so the pixels will not be identical

We have run tests on a wide sample of source images from our repository. We cannot share this test repository on GitHub due to copyright issues, but if you want to run your own tests these automatic lossless checks should simplify that. The full lossless checks can be disabled in production, but we would recommend keeping them enabled if digital preservation is a concern.

Note: our testing has been focused on the source images we ingest, not all possible formats. The :func:`~image_processing.validation.check_image_suitable_for_jp2_conversion` function is run when generating derivatives, and should fail for image formats we have not tested.

See :doc:`jp2_colour_management` for some more background information and recommendations.


Embedded metadata
-----------------

We extract image metadata from the source file to a separate XML file for digital preservation, using `Exiftool`_. Exiftool is a command line tool for reading, writing and editing embedded metadata with very thorough support for image embedded metadata formats.

This separate XML file is stored along with the JP2 in the archive. The metadata in the file is stored in the image metadata format XMP, mapped from whatever formats (EXIF, IPTC etc.) were used in the TIFF file. Exiftool also offers a proprietary XML format which preserves the original format of the metadata fields, but we chose XMP as a widely recognised format for sidecar files, rather than going with a proprietary format that may change in future.

Copying over metadata
~~~~~~~~~~~~~~~~~~~~~

While the extracted metadata is what we rely on for preservation, we also want to have as much of the original metadata as possible in the JP2 image.

Maintaining embedded metadata while converting between image file formats is difficult. All of the image conversion software we've tried had problems with embedded metadata.

- `ImageMagick`_ sometimes produces badly formed metadata in the converted file
- `Pillow`_ by default doesn't copy over any metadata. Embedded metadata related functionality is limited
- `Kakadu`_ only copies over some metadata

Because of this, we don't rely on the image conversion library we use (Pillow) to copy over metadata. Instead, we use Exiftool to copy over metadata after the image is converted, both when converting from JPEG to TIFF and when converting from TIFF to JP2. When copying over to JP2 we map all embedded metadata formats to XMP, as JP2 doesn't have an official standard for storing EXIF.

.. _Exiftool: http://owl.phy.queensu.ca/~phil/exiftool/
.. _Kakadu: http://kakadusoftware.com/
.. _Pillow: http://pillow.readthedocs.io/en/latest/
.. _ImageMagick: http://www.imagemagick.org/