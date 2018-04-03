JP2 colour profiles for digital preservation
============================================

Preservation guidelines
-----------------------

Digital preservation recommendations are that the original colour profile is retained in the preservation copy, and not converted.

    - Specified color space preferred over unspecified or unknown color space.
    - Color space from initial creation preferred to transcoded color space

    -- https://www.loc.gov/preservation/digital/formats/content/still\_preferences.shtml

Note also that colour profile conversion can be lossy.

JP2 conversion details
----------------------

The ``-jp2_space`` parameter on ``kdu_compress`` sets the colour profile in the image metadata, but does not otherwise convert the image - the pixel values remain the same. The ``sRGB`` value sets the colour profile to the sRGB IEC61966-2.1 profile. (This is not the only way to set the colour profile)

Kakadu (and JP2 itself) will not support CYMK images:

    Only three colour channels, R (red), G (green) and B (blue), are supported by the JP2 file format. Alternatively, a luminance image may have exactly one colour channel, Y (luminance).
    --`Kakadu  manual <http://kakadusoftware.com/wp-content/uploads/2014/06/Kakadu.pdf%205.2.1>`__

JPX does support it, but isn't recommended for digital preservation.

JP2 only supports a restricted set of ICC profile features. For example the `sRGB v4 ICC preference profile <http://www.color.org/srgbprofiles.xalter#v4pref>`__ is not supported, and cannot be embedded into a JP2 file using Kakadu. Setting ``-jp2_space sRGB`` on ``kdu_compress`` will erase the embedded profile and so allow it to be converted. But the sRGB IEC61966-2.1 profile thus assigned is sufficiently different that in some cases there is a noticeable tint to the created JP2.


Recommendations
---------------

When using JP2 for preservation, preserve the original colour space where possible, and keep it embedded in the JP2.

Supported RGB colour profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the original TIFF has an RGB colour profile supported by JP2, this is simple. Convert directly from the original TIFF, without any colour conversion beforehand, and do not use the ``-jp2_space`` parameter in ``kdu_compress``.

Monochrome colour spaces
~~~~~~~~~~~~~~~~~~~~~~~~

The conversion process is the same for greyscale and bitonal images as it is for RGB images. JP2 supports single channel colour. Note: bitonal JP2s converted back to TIFFs end up as greyscale TIFFs (but are still visually identical).

Bitonal images do not need colour profiles. Ideally greyscale images should have one - the digital preservation recommendation is Grayscale Gamma 2.2. This will be embedded in the created JP2.

It is possible to convert monochrome images to RGB when compressing to JP2. These three channel JP2s expand to single channel TIFFs. We have historically done this with our monochrome images, originally because a legacy image server did not support single channel JP2s. This is no longer an issue for us (we have tested single channel JP2s with IIPServer and Jpylyzer), so we stick to the original colour mode and profile, as recommended.

RGBA colour spaces
~~~~~~~~~~~~~~~~~~

The ``kdu_compress`` command options we use do not always preserve alpha channel information with RGBA TIFFs. We add the ``-jp2_alpha`` option, which tells kakadu to treat the 4th image component as alpha, but there is still an issue with unassociated alpha channels, which cannot be converted back to TIFF using ``kdu_expand``:

    Kakadu Warning: Alpha channel cannot be identified in a TIFF file since it is of the unassociated (i.e., not premultiplied) type, and these are not supported by TIFF.  You can save this to a separate output file.

As very few of our input images have an alpha channel, and we have not encountered failing cases in live data (as opposed to constructed test data), this is not a priority for us. We just make sure to check RGBA JP2 conversions are lossless, so we will catch any future failing cases.

Colour profiles / modes not supported by JP2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Convert to a wide gamut RGB colour profile supported by JP2 - we use Adobe RGB 1998. This may be lossy, so consider keeping a copy of the original TIFF for preservation.

Images without colour profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ideally, we would work out the closest colour profile for the image and assign that. If this is not possible, either read the technical metadata and find out the profile most commonly used in the scanner/camera, or run tests and visual comparisons on some of the files to see if there is a standard colour profile that makes the least change to the colour. Without a colour profile, images will be assumed to be sRGB by browsers.

If we are not able to calculate a profile, the recommendation is to leave it without one rather than assigning one arbitrarily.

Delivery
~~~~~~~~

Where delivery is the priority, rather than preservation, there are two options:

1. Convert the image to sRGB (and embed the sRGB profile)
2. Keep the image with its original colour profile

Historically, many browsers have not supported colour profiles and have displayed images as if they were all sRGB. This is still the case with some older versions of browsers, especially on mobile platforms. Android only started supporting colour profiles with 8.0. So (1) is the safest option to ensure colour accuracy on all browsers.

However, the latest versions of all major browsers (including Chrome, Edge, Firefox, IE, Safari, and Chrome and Safari on mobile) now support colour profiles (as do many IIIF servers, such as IIP). So with (2) most users would still be able to view images with colour accuracy. Keeping the original colour profile also permits users with wide gamut monitors can see AdobeRGB images with the full depth of colour, rather than being limited to the narrower sRGB gamut.

We use the same JP2 for preservation and delivery, so we have to use (2) in any case, to avoid the lossy conversion to sRGB.

Testing
-------

As well as manual visual checks, our JP2 conversion methods have all been tested by

1. Compressing the TIFF to JP2
2. Validating the JP2 with jpylyzer
3. Expanding the JP2 to a new TIFF
4. Comparing the colour mode, colour profile and pixels of the original and new TIFF

If any of the comparisons are not equal (with the exception of bitonal images, which we expect to produce greyscale TIFFs when converted back), the conversion is not considered lossless. This test ensures we can always return to a visually identical source TIFF file.