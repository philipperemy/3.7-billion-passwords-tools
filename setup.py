import sys

from Cython.Build import cythonize
from setuptools import setup, find_packages

if sys.version_info < (3, 6):
    raise Exception('Must be using Python 3.6 or above.')

# Install cython first.
setup(name='breach',
      version='2.2',
      author='Philippe Remy',
      ext_modules=cythonize("breach/cparser.pyx", language_level="3"),
      packages=find_packages(),
      install_requires=[
          'tqdm',
          'validate-email',
          'click'
      ],
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'breach=breach.cli:cli',
          ],
      }
      )
