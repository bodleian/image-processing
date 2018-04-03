Digital Preservation
--------------------

This package has a strong emphasis on digital preservation, as we want to use lossless JP2s as our preservation master files. It was developed with input from our digital preservation team.

By default it checks:

- the JP2 is valid (using `jpylyzer`_)
- the JP2 can be converted back into a TIFF
- this TIFF has the same pixels as the source TIFF (or the TIFF we converted from the source JPEG)
- this TIFF has the same colour profile and mode as the source image

.. _Jpylyzer: http://jpylyzer.openpreservation.org/

It does not check:

- the technical metadata is correctly copied over to the JP2 (we extract this to a separate file)
- the JP2 displays as expected in viewers
- the JPG to TIFF conversion, if the source file was a JPG (beyond checking the colour profiles match). It is a lossy conversion, so the pixels will not be identical

We have run tests on a wide sample of source images from our repository. We cannot share this test repository on GitHub due to copyright issues, but if you want to run your own tests these automatic lossless checks should simplify that. The full lossless checks can be disabled in production, but we'd recommend keeping them enabled if digital preservation is a concern.

Note: our testing has been focused on the source images we ingest, not all possible formats. The :func:`~image_processing.validation.check_image_suitable_for_jp2_conversion` function is run when generating derivatives, and should fail for image formats we have not tested.

See :doc:`jp2_colour_management` for some more background information and recommendations.
