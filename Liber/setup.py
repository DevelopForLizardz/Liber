"""
 py2app/py2exe build script for MyApplication.

 Will automatically ensure that all build prerequisites are available
 via ez_setup

 Usage (Mac OS X):
     python setup.py py2app

 Usage (Windows):
     python setup.py py2exe
"""

import ez_setup
ez_setup.use_setuptools()

import sys
from setuptools import setup

mainscript = '__main__.py'

if sys.platform == 'darwin':
    extra_options = dict(
        DATA_FILES=['--iconfile'],
        setup_requires=['py2app', 'nose', 'pafy', 'pydub', 'mutagen', 'youtube-dl'],
        app=[mainscript],
        # Cross-platform applications generally expect sys.argv to
        # be used for opening files.
        options=dict(py2app=dict(argv_emulation=True, iconfile='/Users/ryan/Code/Projects/Liber/docs/512x512.icns')),
    )
elif sys.platform == 'win32':
    extra_options = dict(
        DATA_FILES=['--iconfile'],
        setup_requires=['py2exe', 'nose', 'pafy', 'pydub', 'mutagen', 'youtube-dl'],
        app=[mainscript],
    )
else:
    extra_options = dict(
        # Normally unix-like platforms will use "setup.py install"
        # and install the main script as such
        DATA_FILES=['--iconfile'],
        setup_requires=['py2exe', 'nose', 'pafy', 'pydub', 'mutagen', 'youtube-dl'],
        scripts=[mainscript],
    )

setup(
    name="Liber",
    **extra_options
)
