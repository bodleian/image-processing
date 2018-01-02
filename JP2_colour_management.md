# JP2 colour profiles for digital preservation

## Preservation guidelines

Digital preservation recommendations are that the original colour profile is retained in the preservation copy, and not converted.
> - Specified color space preferred over unspecified or unknown color space.
> - Color space from initial creation preferred to transcoded color space

(https://www.loc.gov/preservation/digital/formats/content/still_preferences.shtml) 

Note also that colour profile conversion can be lossy.

## JP2 conversion details

The `-jp2_space` parameter on `kdu_compress` sets the colour profile in the image metadata, but does not otherwise convert the image - the pixel values remain the same. The `sRGB` value sets the colour profile to the sRGB IEC61966-2.1 profile. (This is not the only way to set the colour profile)

Kakadu (and JP2 itself) will not support CYMK images:

> Only three colour channels, R (red), G (green) and B (blue), are supported by the JP2 file format. Alternatively, a luminance image may have exactly one colour channel, Y (luminance).' [Kakadu manual](http://kakadusoftware.com/wp-content/uploads/2014/06/Kakadu.pdf 5.2.1)

JPX does support it, but isn't recommended for digital preservation.

Kakadu only supports a restricted set of ICC profile features. For example the [sRGB v4 ICC preference profile](http://www.color.org/srgbprofiles.xalter#v4pref) is not supported, and cannot be embedded into a jp2 file using Kakadu. Setting `-jp2_space sRGB` on `kdu_compress` will erase the embedded profile and so allow it to be converted. But the sRGB IEC61966-2.1 profile thus assigned is sufficiently different that in some cases there's a noticable tint to the created jp2.

## Recommendations

When using JP2 for preservation, preserve the original colour space where possible, and keep it embedded in the JP2.

### Supported RGB colour profiles
If the original tiff has an RGB colour profile supported by kakadu, this is simple. Convert directly from the original tiff, without any colour conversion beforehand, and don't use the `-jp2_space` parameter in `kdu_compress`.

### Monochrome colour spaces
To be decided

## RGBA colour spaces
The `kdu_compress` command options we use don't always preserve alpha channel information with RGBA tiffs. As very few of our images are RGBA, and so far we haven't encountered failing cases in live data (as opposed to constructed test data), we just make sure to check RGBA JP2 conversions are lossless, and otherwise treat them the same as RGB.

### Colour profiles / spaces not supported by kakadu
To be decided

### Images without colour profiles
To be decided

### Delivery

Where delivery is the priority, rather than preservation, there are two options:

1. Convert the image to sRGB (and embed the sRGB profile)
2. Keep the image with its original colour profile

Historically, many browsers haven't supported colour profiles and just displayed images as if they were all sRGB. This is still the case with some older versions of browsers, especially older mobile ones: e.g. Android only started supporting colour profiles with 8.0. So (1) is the safest option to ensure colour accuracy on all browsers.

However, basically all modern browsers now support colour profiles (as do IIIF servers like IIPImage), and use of legacy browsers will only decrease further with time. So with (2) most users would still be able to view images with colour accuracy. Keeping the original colour profile also means users with wide gamut monitors can see AdobeRGB images with the full depth of colour, rather than being limited to the narrower sRGB gamut.

We use the same JP2 for preservation and delivery, so we have to use (2) in any case, to avoid the lossy conversion to sRGB.