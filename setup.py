from setuptools import setup

with open("README.rst", 'r') as f:
      long_description = f.read()

setup(name='image_processing',
      version='1.8.0',
      description='Digital Bodleian image processing library',
      url='http://github.com/bodleian/image-processing',
      license="MIT",
      long_description=long_description,
      author='Mel Mason',
      author_email='mel.mason@bodleian.ox.ac.uk',
      packages=['image_processing'],
      install_requires=['Pillow', 'jpylyzer']
)
