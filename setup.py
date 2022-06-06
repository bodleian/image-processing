from setuptools import setup

with open("README.rst", 'r') as f:
    long_description = f.read()

setup(name='image_processing',
      version='1.10.0',
      description='Digital Bodleian image processing library',
      url='http://github.com/bodleian/image-processing',
      license="MIT",
      long_description=long_description,
      author='Mel Mason',
      author_email='mel.mason@bodleian.ox.ac.uk',
      packages=['image_processing'],
      install_requires=['Pillow', 'jpylyzer'],
      entry_points={
            'console_scripts': ['convert_tiff_to_jp2=image_processing.entry_points:generate_derivatives_from_tiff',
                                'convert_icc=image_processing.entry_points:convert_icc_profile'
                                ]
      }
      )
