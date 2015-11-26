"""

Liber is a module made for downloading YouTube videos as audio (with support for adding metadata) or video. It is meant
to be part of a graphical application, (which is why GUI.py is a part of this package), however it can be used on its
own.

The name Liber (LIE-bar) comes from the Roman god of freedom 'Liber'

Copyright (C) 2015 Ryan Drew

Liber is free software and can be distributed, used and modified under the restrictions of the MIT license, which should
be included in this package.

Liber is distributed WITHOUT a warranty.

"""


__author__ = 'Ryan Drew'
__version__ = 0.2

import pafy
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
import pydub
import logging
import logging.config
import os
import shutil
import platform
import urllib2
import StringIO
from random import randint

# setup logging
I_am_child = False
for x, y in logging.Logger.manager.loggerDict.items():
    if x == '__main__':
        I_am_child = True
        logger = logging.getLogger('__main___.' + __name__)
        break
if I_am_child is False:
    logger = logging.getLogger(__name__)
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    con = logging.StreamHandler()
    con.setLevel(logging.DEBUG)
    con.setFormatter(formatter)
    logger.addHandler(con)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # makes logger only use stream handler

# pydub logging
l = logging.getLogger("pydub.converter")
l.setLevel(logging.DEBUG)
l.addHandler(logging.StreamHandler())
        
# This bit of code will try to find the "Automatically Add to iTunes folder" and the users DOWNLOADS folder  on the
# system and store it in ITUNES and DOWNLOADS. If it can't be found, then ITUNES/DOWNLOADS will equal None.
# First need to declare the variables for scope purposes
ITUNES = None
ITUNES_TEMP = None
DOWNLOADS = None

if len(platform.mac_ver()[0]) > 0:  # platform.mac_ver()[0] is '' on non OSX systems.
    ITUNES = os.path.expanduser('~/Music/iTunes/iTunes Media/Automatically Add to iTunes.localized')
    ITUNES_TEMP = os.path.expanduser('~/Music/iTunes/iTunes Media')
    try:
        if os.path.exists(ITUNES) is False:
            raise IOError("No such file or directory: {}".format(ITUNES))
        if os.path.exists(ITUNES_TEMP) is False:
            raise IOError("No such file or directory: {}".format(ITUNES_TEMP))
    except IOError:
        logger.warning("Unable to locate 'Automatically Add to iTunes' folder on this system: "
                       "'{}', '{}'".format(platform.mac_ver(), platform.system()))
        ITUNES = None
        ITUNES_TEMP = None

elif platform.system() == 'Windows' and platform.release() != 'XP':
    ITUNES = os.path.expanduser('~/Music/iTunes/iTunes Media/Automatically Add to iTunes.localized')
    ITUNES_TEMP = os.path.expanduser('~/Music/iTunes/iTunes Media')
    try:
        if os.path.exists(ITUNES) is False:
            raise IOError("No such file or directory: {}".format(ITUNES))
        if os.path.exists(ITUNES_TEMP) is False:
            raise IOError("No such file or directory: {}".format(ITUNES_TEMP))
    except IOError:
        logger.warning("Unable to locate 'Automatically Add to iTunes folder' on this system: "
                       "'{}', '{}'".format(platform.system(), platform.release()))
        ITUNES = None
        ITUNES_TEMP = None

elif platform.system() == 'Windows' and platform.release() == 'XP':
    ITUNES = os.path.expanduser('~/My Music/iTunes/iTunes Media/Automatically Add to iTunes.localized')
    ITUNES_TEMP = os.path.expanduser('~/My Music/iTunes/iTunes Media')
    try:
        if os.path.exists(ITUNES) is False:
            raise IOError("No such file or directory: {}".format(ITUNES))
        if os.path.exists(ITUNES_TEMP) is False:
            raise IOError("No such file or directory: {}".format(ITUNES_TEMP))
    except IOError:
        logger.warning("Unable to locate 'Automatically Add to iTunes' folder on this system: "
                       "'{}', '{}'".format(platform.system(), platform.release()))
        ITUNES = None
        ITUNES_TEMP = None

try:
    DOWNLOADS = os.path.expanduser("~/Downloads")  # path to user's downloads folder
    if os.path.exists(DOWNLOADS) is False:
        raise IOError("No such file or directory: {}".format(DOWNLOADS))
except IOError:
    logger.warning("Unable to locate 'Downloads' folder on this system")
    DOWNLOADS = None

METADATA = {"artist": "Artist", "album_artist": "Album Artist", "album": "Album", "date": "Date (Year)",
            "track": "Track Number (x/y)", "genre": "Genre", "TIT1": "Grouping", "disc": "Disc Number (x/y)",
            "TBPM": "BPM", "title": "Title"}

# these variables represent whether Liber should download the video as audio or as a video. See the download function
# below
ID_AUDIO = 0
ID_VIDEO = 1


class MetadataError(Exception):
    """
    Raised when an error occurs with adding metadata to a song
    """

    def __init__(self, message):
        """
        Constructs the error, while allowing a custom message to be used
        """

        super(MetadataError, self).__init__(message)


class YTSong(object):
    """
    Main class. Acts as a way for holding information about song metadata and information.
    Contains methods for downloading, applying, metadata and moving the song to the desired location.
    Any method or attribute starting with a '_' shows that the attribute or method is to not be used/accessed by the
    user and only other methods or attributes that don't start with a '_' will use it. This is done for organization or
    functional purposes
    """

    def __init__(self, url, log=None):
        """
        Create the object.
        :param url: Desired YouTube url
        :param log: Force the use of a desired logger object.
        :return: None
        """

        if log is None:
            self.logger = logger.getChild("'{}'".format(url))
        else:
            self.logger = log

        try:
            self.url = url
            self._pafy = pafy.new(url)
            self.author = self._pafy.author
            self.thumb = self._pafy.thumb
            self.bigThumb = self._pafy.bigthumb
            self.bigThumbHd = self._pafy.bigthumbhd
            self.category = self._pafy.category
            self.description = self._pafy.description
            self.likes = self._pafy.likes
            self.dislikes = self._pafy.dislikes
            self.duration = self._pafy.duration
            self.keywords = self._pafy.keywords
            self.length = self._pafy.length
            self.published = self._pafy.published
            self.rating = self._pafy.rating
            self.title = self._pafy.title
            self.videoId = self._pafy.videoid
            self.viewCount = self._pafy.viewcount
            self.audio = self._pafy.getbestaudio()
            self.video = self._pafy.getbest(preftype="mp4")
            if self.video is None:
                self.video = self._pafy.getbest()
            self.downloadPath = None  # placeholder
            self.destinationPath = None  # placeholder

            self.logger.info("The information and the best audio stream for the YouTube url ({}; title: {}...) "
                             "has been retrieved. Best audio stream located at: {}.".format(url,
                                                                                            self.title[:25],
                                                                                            self.audio.url[:25]))

            self.logger.debug("URL: %s" % url)
            self.logger.debug("Author: %s" % self.author)
            self.logger.debug("Thumb: %s" % self.thumb)
            self.logger.debug("Big thumb: %s" % self.bigThumb)
            self.logger.debug("Big thumb HD: %s" % self.bigThumbHd)
            self.logger.debug("Category: %s" % self.category)
            try:
                self.logger.debug("Description: %s" % self.description[:self.description.index('\n')])
            except ValueError:
                self.logger.debug("Description: %s" % self.description)
            self.logger.debug("Likes: %s" % self.likes)
            self.logger.debug("Dislikes: %s" % self.dislikes)
            self.logger.debug("Duration: %s" % self.duration)
            self.logger.debug("Keywords: %s" % self.keywords)
            self.logger.debug("Length: %s" % self.length)
            self.logger.debug("Published: %s" % self.published)
            self.logger.debug("Rating: %s" % self.rating)
            self.logger.info("Title: %s" % self.title)
            self.logger.debug("Video ID: %s" % self.videoId)
            self.logger.debug("ViewCount: %s" % self.viewCount)

        except urllib2.URLError:
            self.logger.error("Failed to open given url: %s" % url, exc_info=True)
            raise
        except TypeError:
            self.logger.error("Failed to open given url: %s" % url, exc_info=True)
            raise
        except KeyError:
            self.logger.error("Failed to open given url: %s" % url, exc_info=True)
            raise
        except ValueError:
            self.logger.error("Failed to open given url: %s. It is invalid" % url, exc_info=True)
            raise

    def get_artwork(self, thumb):
        """
        Opens the given album artwork url and returns the image data.
        :param thumb: url to thumbnail
        :return: The image data for the url
        """

        self.logger.info("Fetching album artwork at: %s" % thumb)

        if os.path.exists(thumb) is True:
            try:
                response = open(thumb).read()
                self.logger.info("Album artwork retrieved")
                return response
            except:
                self.logger.error("Failure to retrieve album artwork (which was presumed to be a file path",
                                  exc_info=True)
                raise
        else:
            try:
                response = urllib2.urlopen(thumb).read()
                self.logger.info("Album artwork retrieved")
                return response
            except:
                self.logger.error("Failure to retrieve album artwork (which pas presumed to be a url", exc_info=True)
            raise
    
    def _place_holder_callback(self, *args, **kwargs):
        """
        Used in the _add_metadata_and_convert function if the callback was not given. Prevents a TypeError from being
        raised otherwise
        """

        # putting these into lists allows for easier string formatting and reading
        list_args = [i for i in args]
        list_kwargs = [kwargs]

    def add_metadata_and_convert(self, song_path, metadata=None, album_artwork=None, callback=_place_holder_callback):
        """
        Uses pydub and mutagen to add specified metadata to the given song and uses pydub to convert the given song to
        mp3
        :param song_path: Location of the song that needs to be opened
        :param metadata: metadata to add to the song, is a dictionary where keys are in
        ffmpeg format (see self.METADATA)
        :param album_artwork: file path that leads to a jpeg, png or url.
        :param callback: Called and passed a numeric value that represents the progress of this function
        :return: none
        """

        self.logger.info("Adding metadata to %s" % song_path)
        self.logger.debug("Album Artwork type: %s, length: %s" % (type(album_artwork),
                                                                  len(album_artwork) if album_artwork is
                                                                  not None else "n/a"))
        message = "None"
        if metadata is not None:
            message = ""
            for key, value in metadata.items():
                if len(value) > 0:
                    message += "{}: '{}' \n".format(key, value)
                else:
                    del metadata[key]

        self.logger.debug("Metadata: "+message)

        callback(0.3)
        try:
            song = pydub.AudioSegment.from_file(song_path, self.audio.extension)
            song_path = song_path[:-4] + ".mp3"  # removes extension from the given song path and replaces it with .mp3
            if len(metadata) > 0:
                song.export(song_path, format='mp3', tags=metadata)
            else:
                song.export(song_path, format='mp3')

            callback(0.4)

            if album_artwork is not None:
                self.logger.info("Album artwork has been given")
                song = MP3(song_path, ID3=ID3)

                aa_extension = album_artwork[-3:]
                self.logger.debug("Album artwork extension: {}".format(aa_extension))
                if aa_extension in ['jpg', 'png']:
                    song.tags.add(
                        APIC(
                            encoding=3,  # 3 is for utf-8
                            # this specifies what type of image to use
                            mime='image/{}'.format('jpeg' if aa_extension == 'jpg' else aa_extension),
                            type=3,  # this is for a cover image
                            desc=u'Cover',
                            data=open(album_artwork).read() if os.path.exists(album_artwork) is True else
                            StringIO.StringIO(self.get_artwork(album_artwork)).read()
                        )
                    )
                    song.save()
                    callback(0.7)

                else:
                    raise MetadataError("Given album artwork located at %s is not a png or jpg." % album_artwork)
            else:
                self.logger.info("No album artwork given to add as metadata")

            try:  # when pydub song is exported, it doesn't cleanup the old audio file.
                old_song_path = song_path[:-4]+"."+self.audio.extension  # old song is not mp3- must use old extension
                self.logger.info("Removing old {} file located at {}".format(self.audio.extension, old_song_path))
                os.remove(old_song_path)
                callback(0.9)
            except OSError:
                self.logger.warning("Failed to remove old song")

        except:
            self.logger.error("Failed to add metadata and/or convert to mp3", exc_info=True)
            raise
        else:
            self.logger.info("Metadata adding process and converting process completed.")
            callback(1)

    def download(self, path, temp_path, downloadType=ID_AUDIO, metadata=None, album_artwork=None,
                 callbackDown=_place_holder_callback, callbackMetadata=_place_holder_callback):
        """
        Method to download given video's audio to 'path' and add 'metadata' to it
        :param path: Path to where the user wants the video to be downloaded (directory)
        :param downloadType: ID_AUDIO=Download as audio, ID_VIDEO=download as video.
        :param metadata: Metadata to add to the song
        :param album_artwork: Path to png or jpeg.
        :param temp_path: Song will be downloaded to temp_path and then moved to path
        :param callbackDown: callback to send download progress information to
        :param callbackMetadata: callback to send adding metadata progress information to (ignored if the downloadType
            is ID_VIDEO
        :return: "Song downloaded and converted. Located at: %s" % path
        """

        self.logger.info("Starting download to the directory: %s as %s."
                         "Download will be moved to %s after it finishes downloading" % (path, downloadType, temp_path))
        self.logger.debug("Path: {}, type: {}, temp_path: {}, metadata: {}, album artwork: {}".format(path, temp_path,
                                                                                                      downloadType,
                                                                                                      metadata,
                                                                                                      album_artwork))

        try:
            if os.path.exists(path) is False:
                raise IOError("No such file or directory: {}".format(path))
            elif os.path.isdir(path) is False:
                raise IOError("Not a directory: {}".format(path))
            elif os.path.exists(temp_path) is False:
                raise IOError("No such file or directory: {}".format(temp_path))
            elif os.path.isdir(temp_path) is False:
                raise IOError("Not a directory: {}".format(temp_path))
            else:
                if downloadType == ID_AUDIO:
                    self.logger.info("Downloading the video as audio")
                    # adding the random int prevents multiple videos from being mixed up together during a
                    # download session
                    random_int = str(randint(0, 100))
                    file_name = '/Youtube_Download-'+self.title
                    self.downloadPath = temp_path + file_name + random_int + "." + self.audio.extension
                    self.destinationPath = path + file_name + '.mp3'
                    self.logger.debug("Download path: {}".format(self.downloadPath))
                    self.logger.debug("Destination path: {}".format(self.destinationPath))

                    self.logger.info("Downloading audio now")
                    self.audio.download(self.downloadPath, quiet=True, callback=callbackDown)
                    self.logger.info("Audio download complete")
                    self.logger.info("Adding metadata to song. Running self._add_metadata_and_convert")
                    self.add_metadata_and_convert(self.downloadPath, metadata=metadata, album_artwork=album_artwork,
                                                  callback=callbackMetadata)

                    self.logger.info("Moving song to its destination located at {}".format(self.destinationPath))
                    shutil.move(self.downloadPath[:-3]+'mp3', self.destinationPath)

                    self.logger.info("Download process complete")
                elif downloadType == ID_VIDEO:
                    self.logger.info("Downloading the video as a video")
                    random_int = str(randint(0, 100))
                    if metadata['title'] == '':
                        metadata['title'] = self.title
                    file_name = '/'+metadata['title']
                    self.downloadPath = temp_path + file_name + random_int + "." +self.video.extension
                    self.destinationPath = path + file_name + "." + self.video.extension
                    self.logger.debug("Download path: {}".format(self.downloadPath))
                    self.logger.debug("Destination path: {}".format(self.destinationPath))

                    self.logger.info("Downloading video now")
                    self.video.download(self.downloadPath, quiet=True, callback=callbackDown)
                    self.logger.info("Video download complete")

                    self.logger.info("Moving video to its destination located at {}".format(self.destinationPath))
                    shutil.move(self.downloadPath, self.destinationPath)

                    self.logger.info("Download process complete")
                else:
                    raise TypeError("Invalid download type: {}. Was expecting either a 0 for audio or 1 for "
                                    "video".format(downloadType))
        except:
            self.logger.error("A problem occurred while downloading: {} from: {}. Download has been stopped.".format(
                self.title, self.url), exc_info=True)
            raise

if __name__ == '__main__':
    song = YTSong('www.youtube.com/watch?v=dQw4w9WgXcQ')
    song.download(DOWNLOADS, DOWNLOADS, album_artwork=song.bigThumb)
