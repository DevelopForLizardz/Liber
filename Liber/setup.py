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
import os
from setuptools import setup

mainscript = '__main__.py'
iconfile = os.getcwd()+'/docs/512x512.icns'
datafiles = [os.getcwd()+'/docs']

if sys.platform == 'darwin':
    extra_options = dict(
        setup_requires=['py2app', 'nose', 'pafy', 'pydub', 'mutagen', 'youtube-dl'],
        app=[mainscript],
        # Cross-platform applications generally expect sys.argv to
        # be used for opening files.
        options=dict(py2app=dict(argv_emulation=True, iconfile=iconfile, resources=datafiles)))
        
elif sys.platform == 'win32':
    extra_options = dict(
        setup_requires=['py2exe', 'nose', 'pafy', 'pydub', 'mutagen', 'youtube-dl'],
        app=[mainscript],
        options=dict(py2app=dict(iconfile=iconfile, resources=datafiles))
    )
else:
    extra_options = dict(
        # Normally unix-like platforms will use "setup.py install"
        # and install the main script as such
        setup_requires=['py2exe', 'nose', 'pafy', 'pydub', 'mutagen', 'youtube-dl'],
        options=dict(py2app=dict(iconfile=iconfile, resources=datafiles)),
        scripts=[mainscript],
    )

setup(
    name="Liber",
    **extra_options
)
