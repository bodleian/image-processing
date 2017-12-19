from setuptools import setup

with open("README.md", 'r') as f:
      long_description = f.read()

setup(name='image_processing',
      version='1.4.0',
      description='Image processing library',
      url='http://gitlab.bodleian.ox.ac.uk/digital.bodleian/image-processing',
      #license="",
      long_description=long_description,
      author='Bodleian Libraries',
      #author_email='',
      packages=['image_processing'],
      install_requires=['Pillow', 'jpylyzer', 'python-xmp-toolkit']
)
