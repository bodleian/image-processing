from setuptools import setup

with open("README.md", 'r') as f:
      long_description = f.read()

setup(name='image_processing',
      version='1.7.0',
      description='Digital Bodleian image processing library',
      url='http://gitlab.bodleian.ox.ac.uk/digital.bodleian/image-processing',
      license="MIT",
      long_description=long_description,
      author='Mel Mason',
      author_email='mel.mason@bodleian.ox.ac.uk',
      packages=['image_processing'],
      install_requires=['Pillow', 'jpylyzer', 'python-xmp-toolkit']
)
