JPEG2000 Profile
================

.. _kdu_compress-options:

Kakadu compression parameters
-----------------------------

Digital Bodleian uses the following ``kdu_compress`` options (:attr:`~image_processing.kakadu.DEFAULT_LOSSLESS_COMPRESS_OPTIONS`) for lossless JP2 conversion:

- ``Clevels=6`` Resolution levels. At least 3 are recommended to help compression. After that, the aim is to have the lowest resolution sub-image be roughly thumbnail-sized, so the optimal value is dependent on image size. [#wellcome]_
- ``Clayers=6`` Quality layers. More layers can help with quicker decompression; you can decode only a subset of the layers when dealing with lower resolution images where quality decrease isn't noticed. [#wellcome]_
- ``Cprecincts={256,256},{256,256},{128,128}`` Precinct sizes for each resolution level. The last value applies to all subsequent levels [#kdugist]_
- ``Stiles={512,512}`` Tile size [#kdugist]_
- ``Corder=RPCL`` Progression order of Resolution, Position, Component, Layer. This defines which sub-images occur first in the datastream. Having resolution first optimises for fast decompression of thumbnails]. [#wellcome]_  Performance analysis by the British Library [#britishlib]_ recommended RPCL for their use case.
- ``ORGgen_plt=yes`` Include packet length information in the header of all tile-parts [#kdugist]_
- ``ORGtparts=R`` Controls the division of each tile's packets into tile-parts [#kdugist]_
- ``Cblk={64,64}`` Code-block size [#kdugist]_
- ``Cuse_sop=yes`` Include SOP markers. Limits the damage of bit flipping errors to a single block [#czechlib]_
- ``Cuse_eph=yes`` Include EPH markers. Limits the damage of bit flipping errors to a single block [#czechlib]_
- ``-flush_period 1024`` allows streaming when writing to output file. The value is dependent on tile size and sometimes precinct size [#kdugist]_
- ``Creversible=yes`` Use reversible wavelet and component transforms (required for losslessness) [#wellcome]_
- ``-rate -`` Compression rates for each quality layer. An initial value of ``-`` is needed to ensure true losslessness, as otherwise some data may be discarded. Subsequent numbers can be added to specify bit-rates for each of the lower quality layers - if they're all left unspecified, as they are here, "an internal heuristic determines a lower bound and logarithmically spaces the layer rates over the range" [#kdugist]_

For RGBA images we add:

- ``-jp2_alpha`` Treat the 4th image component as alpha [#kdugist]_

References
----------

.. [#wellcome] `JPEG 2000 as a Preservation and Access Format for the Wellcome Trust Digital Library <http://wellcomelibrary.org/content/documents/22082/JPEG2000-preservation-format.pdf>`_
.. [#kdugist] `Andrew Hankinson's notes on kdu_compress options <https://gist.github.com/ahankinson/4945722>`_
.. [#czechlib] `JPEG 2000 Specifications for The National Library of the Czech Republic <https://www.iiifserver.com/doc/NationalLibraryOfTheCzechRepublicJPEG2000Profile.pdf>`_
.. [#britishlib] `British Library JPEG 2000 profile <https://www.dpconline.org/docs/miscellaneous/events/524-jp2knov2010martin/file>`_

- `JPEG 2000 seminar – edited highlights #1 <http://blog.wellcomelibrary.org/2010/11/jpeg-2000-seminar-edited-highlights-1/>`_
- `IIPImage & An Analysis of JPEG2000 Encoding Parameters <https://www.dpconline.org/docs/miscellaneous/events/1358-2014-nov-jp2k-ruven/file>`_
- `JPEG 2000 profiles – examples from a range of institutions <https://www.dpconline.org/docs/miscellaneous/events/529-jp2knov2010parametercomparisonchart/file>`_
- `Diva.js JPEG 2000 encoding with Kakadu <https://github.com/DDMAL/diva.js/wiki/JPEG-2000-encoding-with-Kakadu>`_
- `JPEG2000 Implementation at Library and Archives Canada <https://www.museumsandtheweb.com/mw2007/papers/desrochers/desrochers.html>`_

Note: most of these are from around 2010 - more recent examples of profiles would be welcome.