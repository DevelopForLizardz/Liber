__author__ = 'Ryan Drew'

import logging
import logging.config
import wx

logging.config.dictConfig({
    'version': 1,
    'propagate': False,
    'disable_existing_loggers': False,

    'formatters': {
        'file': {
            'format': '%(levelname)s:%(asctime)s:%(name)s:%(message)s',
            'datefmt': "%m/%d/%Y %I:%M:%S %p"
        },
        'stream': {
            'format': '%(levelname)s:%(name)s:%(message)s'
        }
    },

    'handlers': {
        'stream': {
            'level': 'INFO',
            'formatter': 'stream',
            'class': 'logging.StreamHandler'
        },

        'file': {
            'level': 'DEBUG',
            'formatter': 'file',
            'class': 'logging.FileHandler',
            'filename': 'log.txt'
        }
    },

    'loggers': {
        '': {
            'handlers': ['file', 'stream'],
            'level': 'DEBUG',
        },

    }
})

logger = logging.getLogger(__name__)

wxApp = wx.App()
import GUI
wxFrame = GUI.MainFrame(None)
wxApp.MainLoop()

# OSError raised when ffmpeg cannot be found
