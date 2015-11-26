"""
This is module is a GUI created for the Liber module included in this package. It is intended to be used
with the Liber module only.

Copyright (C) Ryan Drew 2015

This module is free software and can be distributed, used and modified under the restrictions of the MIT license, which
should be included in this package.
"""

__author__ = 'ryan'
__version__ = 0.2

import wx
import wx.lib.scrolledpanel as scrolled
import logging
import threading
import StringIO
import Liber
import platform
import os
import sys


# this controls the size of each individual tile and the size that album artwork will be scaled to (w, h)
TILE_SIZE = [wx.DisplaySize()[0] * (2.0/3.0), 160]  # 1900
ALBUM_ART_SIZE = (120, 90)

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


# the following sets up a change album artwork event used to change the album artwork of a tile. Called by multiple
# threads in the Tile Class
myEVT_CHANGE_AA = wx.NewEventType()
EVT_CHANGE_AA = wx.PyEventBinder(myEVT_CHANGE_AA, 1)


class ChangeAAEvent(wx.PyCommandEvent):
    """
    Event to signal that the album artwork in a Tile needs to be changed
    """

    def __init__(self, etype, eid, value=None):
        """
        Create the event object
        """

        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

    def GetValue(self):
        """
        Returns the value from the event
        """

        return self._value


# the following sets up a change progress bar event that is used to change the progress bar of a tile. Called through
# the download method.
myEVT_UPDATE_PROGRESSBAR = wx.NewEventType()
EVT_UPDATE_PROGRESSBAR = wx.PyEventBinder(myEVT_UPDATE_PROGRESSBAR, 1)


class UpdateProgressBarEvent(wx.PyCommandEvent):
    """
    Event to signal that the progress bar in a tile needs to be updated/changed
    """

    def __init__(self, etype, eid, value=None):
        """
        Create the event object
        """

        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

    def GetValue(self):
        """
        Returns the value from the event
        """

        return self._value


# the following sets up a reset progress bar and download button event that is used to change their values to their
# defaults after a delay. Called whenever the progress bar's value is 100
myEVT_RESET_PROGRESSBAR_AND_DOWLOADBUTTON = wx.NewEventType()
EVT_RESET_PROGRESSBAR_AND_DOWNLOADBUTTON = wx.PyEventBinder(myEVT_RESET_PROGRESSBAR_AND_DOWLOADBUTTON, 1)


class ResetProgressBarAndDownloadButtonEvent(wx.PyCommandEvent):
    """
    Event to signal that the progress bar and the download button need to reset to their default values
    """

    def __init__(self, etype, eid, value=None):
        """
        Create the event object
        """

        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

    def GetValue(self):
        """
        Returns the value from the event
        """

        return self._value


class Tile(wx.Panel):
    """
    Main GUI Element. Is added into the MainFrame. Pairs with a YTSong class and handles the static texts, text
    controls, images and downloading (including progress bars).
    """

    def __init__(self, url, parent, *args, **kwargs):
        """
        Create the Tile. Parent is expected to be a MainFrame, url is a valid youtube url to be passed to pafy
        :param url: URL to bind to through Liber
        :param parent: Parent to the Panel (mainly a Frame class, which is defined down below
        :param: args: args to pass to the super call
        :param: kwargs: kwargs to pass to the super call. If the key 'parentLogger' is found, it will be used as this
        the parent logger and the key/value pair will be taken out of kwargs when passed to the super.
        """

        try:
            self.logger = kwargs["parentLogger"].getChild("Tile:%s" % url[-11:])
            del kwargs["parentLogger"]
        except KeyError:
            self.logger = logger.getChild("Tile:%s" % url[-11:])
        # this needs to be added, so that in the case of a TypeError, the logger key will still be
        # removed from  the kwargs and a logger will still be obtained
        except TypeError:
            self.logger = logger.getChild("Tile:%s" % url[-11])
            del kwargs["parentLogger"]

        self.logger.info("Constructing")
        super(Tile, self).__init__(parent, *args, **kwargs)
        self.URL = url
        self.enableDownloads = True
        if Liber.ITUNES is not None:
            self.downloadPath = Liber.ITUNES
            self.tempDownloadPath = Liber.ITUNES_TEMP
        elif Liber.DOWNLOADS is not None:
            self.downloadPath = Liber.DOWNLOADS
            self.tempDownloadPath = Liber.DOWNLOADS
        else:
            self.downloadPath = None
            self.tempDownloadPath = None
        self.logger.debug("Video download path: {}, Video temporary download path: {}".format(self.downloadPath,
                                                                                              self.tempDownloadPath))
        self.downloadType = Liber.ID_AUDIO
        self.logger.debug("Video download type set to its default - Liber.ID_AUDIO")

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.metadataSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.Bind(EVT_CHANGE_AA, self.onChangeAA)
        self.Bind(EVT_UPDATE_PROGRESSBAR, self.onUpdatePB)
        self.Bind(EVT_RESET_PROGRESSBAR_AND_DOWNLOADBUTTON, self.onReset)

        # Assign metadata. Must be done like this to prevent this tiles metadata from being assigned the same memory
        # location as Liber.METADATA
        self.metadata = {}
        for x, y in Liber.METADATA.items():
            self.metadata[x] = y

        try:
            self.logger.info("Paring with a YTSong class")
            self.YTSong = Liber.YTSong(url, log=self.logger.getChild("Liber"))
            self.logger.info("Paring complete")
        except Exception, e:
            self.logger.error("Failure to pair with a YTSong class", exc_info=True)
            errorSt = wx.StaticText(self, label="Failure to obtain video: %s" % e)
            errorSt.Center()
            dialog = wx.MessageDialog(self, "Error", "Failure to obtain the video: %s" % e, style=wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            raise

        self.logger.info("Pulling album artwork from video's thumbnail.")
        # location of where the album artwork is on the users' system (if file) or a URL
        self.artworkSource = self.YTSong.thumb
        self.artworkImage = wx.EmptyImage(wx.BITMAP_TYPE_ANY)
        self.artwork = wx.StaticBitmap(self, wx.ID_ANY, wx.EmptyBitmap(ALBUM_ART_SIZE[0], ALBUM_ART_SIZE[1]))
        self.worker(self.changeAAThread, (self.YTSong.thumb,), {})

        self.metadataSizer.Add(self.artwork, proportion=0, flag=wx.ALIGN_LEFT)
        self.metadataSizer.Add((10, -1))

        num_of_columns = 4.0
        max_column_items = 4.0
        column_items = 0
        vSizer = wx.BoxSizer(wx.VERTICAL)
        LINE_SIZE = (TILE_SIZE[0] - (self.artwork.GetSize()[0] + 10*4)) / num_of_columns
        for x, y in self.metadata.items():
            stLabel = y+':'
            tcSize = (LINE_SIZE - self.GetTextExtent(stLabel)[0], -1)
            self.metadata[x] = [wx.StaticText(self, wx.ID_ANY, label=stLabel),
                                wx.TextCtrl(self, wx.ID_ANY, size=tcSize)]

            hSizer = wx.BoxSizer(wx.HORIZONTAL)
            hSizer.Add(self.metadata[x][0], proportion=0, flag=wx.ALIGN_LEFT)
            hSizer.Add(self.metadata[x][1], proportion=0, flag=wx.ALIGN_RIGHT)
            vSizer.Add(hSizer)
            vSizer.Add((-1, 5))  # a little bit of padding in my life...
            column_items += 1

            # add the current sizer to the metadata sizer, create a new vertical sizer, reset column_items and
            # add one to the columns
            if column_items == max_column_items:
                self.metadataSizer.Add(vSizer)
                self.metadataSizer.Add((10, -1))
                vSizer = wx.BoxSizer(wx.VERTICAL)
                column_items = 0
        # need to do a little bit of cleanup, the loop was mainly used for laziness/convenience.
        else:
            self.radioIT = wx.RadioButton(self, wx.ID_ANY, label="iTunes")
            self.radioIT.SetValue(True)
            self.Bind(wx.EVT_RADIOBUTTON, self.onChangeDownLociTunes, self.radioIT)
            self.radioDownload = wx.RadioButton(self, wx.ID_ANY, label="Downloads")
            self.Bind(wx.EVT_RADIOBUTTON, self.onChangeDownLocDownloads, self.radioDownload)
            self.radioDownloadPath = wx.RadioButton(self, wx.ID_ANY, label="Custom")
            self.radioDownloadPath.Bind(wx.EVT_RADIOBUTTON, self.onChooseDownloadPath, self.radioDownloadPath)
            stDownloadLoc = wx.StaticText(self, wx.ID_ANY, label="Download to:")

            objects = [stDownloadLoc, self.radioIT, self.radioDownload, self.radioDownloadPath]
            object_sizes = [self.GetTextExtent(stDownloadLoc.Label)[0], self.radioIT.GetSize()[0],
                            self.radioDownload.GetSize()[0], self.radioDownloadPath.GetSize()[0], ]
            vSizer = self.sizeElementsInAColumn(objects, object_sizes, LINE_SIZE, vSizer, padding=(0, 0))

            if Liber.ITUNES is None:
                self.radioIT.Disable()
                self.radioDownload.SetValue(True)
            if Liber.DOWNLOADS is None:
                self.radioDownload.Disable()
                self.radioDownloadPath.SetValue(True)

            stChangeAA = wx.StaticText(self, label="Change Album Artwork: ")
            self.btAAPath = wx.Button(self, wx.ID_ANY, label="From File", size=(wx.Button.GetDefaultSize()[0],
                                                                                self.GetTextExtent("Fl")[1]))
            self.btAAPath.Bind(wx.EVT_BUTTON, self.onChooseAAPath, self.btAAPath)
            self.btAAURL = wx.Button(self, wx.ID_ANY, label="From URL", size=(wx.Button.GetDefaultSize()[0],
                                                                              self.GetTextExtent("FURL")[1]))
            self.btAAURL.Bind(wx.EVT_BUTTON, self.onChooseAAURL, self.btAAURL)
            self.btAAThumb = wx.Button(self, wx.ID_ANY, label="Thumbnail", size=(wx.Button.GetDefaultSize()[0],
                                                                                 self.GetTextExtent("Tlb")[1]))
            self.btAAThumb.Bind(wx.EVT_BUTTON, self.onChooseAAThumb, self.btAAThumb)
            objects = [stChangeAA, self.btAAPath, self.btAAURL, self.btAAThumb]
            object_sizes = [self.GetTextExtent(stChangeAA.Label)[0], self.btAAPath.GetSize()[0],
                            self.btAAURL.GetSize()[0], self.btAAThumb.GetSize()[0]]

            column_items += 1
            if column_items == max_column_items or len(vSizer.GetChildren()) > 1:
                self.metadataSizer.Add(vSizer)
                self.metadataSizer.Add((10, -1))
                vSizer = wx.BoxSizer(wx.VERTICAL)
            else:
                vSizer.Add((-1, 5))

            # this bit of code will go through the object_sizes and determine how many of the objects it can fit
            # in the space of LINE_SIZE.
            vSizer = self.sizeElementsInAColumn(objects, object_sizes, LINE_SIZE, vSizer)
            self.metadataSizer.Add(vSizer, proportion=0)
            self.mainSizer.Add(self.metadataSizer)
            self.mainSizer.Add((-1, 5))

            stDownloadAs = wx.StaticText(self, wx.ID_ANY, label="as")
            # adding the wx.RB_GROUP allows for a these radio buttons to be pressed along with the previous radio
            # buttons. this way pressing on one of the previous radio buttons does not 'de-press' any of these radio
            # buttons
            self.radioAudio = wx.RadioButton(self, wx.ID_ANY, label="music", style=wx.RB_GROUP)
            self.radioAudio.SetValue(True)
            self.Bind(wx.EVT_RADIOBUTTON, self.onChangeDownloadType, self.radioAudio)
            self.radioVideo = wx.RadioButton(self, wx.ID_ANY, label="video.")
            self.Bind(wx.EVT_RADIOBUTTON, self.onChangeDownloadType, self.radioVideo)
            self.progressBar = wx.Gauge(self, id=wx.ID_ANY, range=100, size=(TILE_SIZE[0], -1), style=wx.GA_HORIZONTAL)
            self.btDownload = wx.Button(self, id=wx.ID_ANY, label="")
            self.updateDownloadLabel()
            self.btDownload.Bind(wx.EVT_BUTTON, self.download, self.btDownload)

            hSizer = wx.BoxSizer(wx.HORIZONTAL)
            hSizer.Add(self.btDownload, flag=wx.ALIGN_LEFT)
            hSizer.Add((5, -1))

            hSizer2 = wx.BoxSizer(wx.HORIZONTAL)
            hSizer2.Add(stDownloadAs)
            hSizer2.Add(self.radioAudio)
            hSizer2.Add(self.radioVideo)
            vWrapper = wx.BoxSizer(wx.VERTICAL)
            vWrapper.Add((-1, 5))
            vWrapper.Add(hSizer2)

            hSizer.Add(vWrapper)
            self.mainSizer.Add(hSizer)
            self.mainSizer.Add(self.progressBar)
            self.mainSizervWrapper = wx.BoxSizer(wx.HORIZONTAL)
            self.mainSizervWrapper.Add(self.mainSizer)
            self.mainSizervWrapper.Add((20, -1))

            self.SetSizer(self.mainSizervWrapper)
            self.SetSize(TILE_SIZE)
            self.logger.info("Construction finished.")

    def sizeElementsInAColumn(self, objects, object_sizes, line_size, vSizer, padding=(-1, 7)):
        """
        This is a recursive function that will take in the object_sizes and determine based on that how many
        objects it can fit in the space of line_size. These objects are added to a horizontal box sizer and that box
        sizer is then added to vSizer. Then, this function will call itself once again, so that it will be able to
        add multiple rows of items with different amounts of objects to vSizer. vSizer is then returned when the
        recursion has finished.
        :param objects: Objects to add to vSizer
        :param object_sizes: The sizes of the objects (width)
        :param line_size: The amount of space the objects have to fit in/ their constraint (width)
        :param vSizer: The vertical sizer that the objects and horizontal sizers are added to.
        :param padding: Extra padding to add between each element in the vSizer (vertical padding)
        :return: the finished vSizer with all the objects in it.
        """

        if len(objects) == 0:  # terminating parameter
            return vSizer
        else:
            # starts by trying to add as many objects as it can to the horizontal sizer, then works its way back,
            # removing one object at a time
            for x in range(len(objects) + 1)[::-1]:
                if sum(object_sizes[:x]) + 10 < line_size:
                    hSizer = wx.BoxSizer(wx.HORIZONTAL)
                    for y in objects[:x]:
                        hSizer.Add(y)
                        hSizer.Add((5, -1))

                    vSizer.Add(hSizer)
                    vSizer.Add(padding)
                    vSizer.Layout()
                    # start recursion
                    vSizer = self.sizeElementsInAColumn(objects[x:], object_sizes[x:], line_size, vSizer)
                    return vSizer

    def updateDownloadLabel(self, label=None):
        """
        Changes self.btDownload's label either the given string or to the current download path
        :param label: String to write to btDownload's label
        """

        if label is None:
            label = "Download to {}".format(self.downloadPath if self.downloadPath != Liber.ITUNES else "iTunes")
        self.logger.debug("Updating the download button's label to: {}".format(label))
        self.btDownload.SetLabel(label)
        self.btDownload.SetSize(self.btDownload.GetEffectiveMinSize())
        self.mainSizer.Layout()

    def worker(self, function, args, kwargs):
        """
        Opens up a new thread, which opens up another process to perform a certain task
        :param function: function to run
        :param args: args to be passed to function
        :param kwargs: kwargs to be passed to function
        """

        self.logger.info("Worker process started. Function: %s" % function)

        thread = threading.Thread(target=function, args=args, kwargs=kwargs)
        thread.start()

    def onReset(self, event):
        """
        Resets the progress bar and download button to their default values.
        """

        self.logger.info("EVT_RESET_PROGRESSBAR_AND_DOWNLOADBUTTON detected. Resetting values.")
        self.updateDownloadLabel()
        self.btDownload.Enable()
        self.progressBar.SetValue(0)

    def resetPBandDBThread(self):
        """
        Thread that waits a certain amount of seconds and then posts a EVT_RESET_PROGRESSBAR_AND_DOWNLOADBUTTON event
        """

        sleep_time = 6
        self.logger.info("Reset progressbar and download button thread started. Sleeping {} seconds".format(sleep_time))
        wx.Sleep(sleep_time)
        self.logger.info("{} seconds up. Posting EVT_RESET_PROGRESSBAR_AND_DOWNLOADBUTTON".format(sleep_time))
        evt = ChangeAAEvent(myEVT_RESET_PROGRESSBAR_AND_DOWLOADBUTTON, -1)
        wx.PostEvent(self, evt)

    def onChangeAA(self, event):
        """
        Called when a change aa event is called. Gets the value from the event and changes the album artwork data
        to that value
        """

        self.logger.info("EVT_CHANGE_AA event detected. Changing album artwork.")
        self.artworkImage.LoadStream(StringIO.StringIO(event.GetValue()))
        self.artworkImage.Rescale(*ALBUM_ART_SIZE)
        self.artwork.SetBitmap(wx.BitmapFromImage(self.artworkImage))
        self.Refresh()

    def changeAAThread(self, image):
        """
        Pulls album art image. Change aa event is posted to tell the parent to take the given data and apply it to
        the album artwork image. The source of the image (url/file path) is stored.
        :param image: can either be a url or a file path to a jpg/png.
        """

        self.logger.info("Changing album art image to: '%s'" % image)

        try:
            self.artworkSource = image
            artworkData = self.YTSong.get_artwork(image)
            self.logger.info("Obtaining album art was a success. Positing event")
            evt = ChangeAAEvent(myEVT_CHANGE_AA, -1, artworkData)
            wx.PostEvent(self, evt)
        except:
            self.logger.warning("Failure to obtain image")
            self.artworkSource = None
            bitmap = wx.EmptyBitmap(ALBUM_ART_SIZE)
            memDC = wx.MemoryDC()
            memDC.SelectObject(bitmap)
            memDC.DrawText("F", (ALBUM_ART_SIZE[0] - memDC.GetTextExtent("F")[0]) / 2,
                           (ALBUM_ART_SIZE[1] - memDC.GetTextExtent("F")[1] / 2))
            # take the selected bitmap out of memory
            memDC.SelectObject(wx.NullBitmap)
            image = wx.ImageFromBitmap(bitmap)
            data = image.GetAlphaData()
            evt = ChangeAAEvent(myEVT_CHANGE_AA, -1, data)
            wx.PostEvent(self, evt)

    def onChooseAAPath(self, event):
        """
        Opens up a dialog that asks a user for a path to a jpg or png image, then tells a worker thread to change
        the album artwork to the user's input
        """

        self.logger.info("Choose album artwork (path) event triggered. Opening a dialog to get user input")

        openFileDialog = wx.FileDialog(self, "Open a jpg/png image for the album artwork.", "", "",
                                       "JPG files (*.jpg)|*.jpg|PNG files (*.png)|*.png",
                                       wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if openFileDialog.ShowModal() != wx.ID_CANCEL:
            self.worker(self.changeAAThread, (openFileDialog.GetPath(),), {})
            self.logger.info("Album artwork location changed. New album artwork path is: {}".format(
                openFileDialog.GetPath()))
        else:
            self.logger.info("Choose album artwork (path) event canceled. ")

    def onChooseAAURL(self, event):
        """
        Opens up a dialog that asks a user for a url to a jpg or png image, then tells a worker thread to change
        the album artwork to the user's input
        """

        self.logger.info("Choose album artwork (URL) event triggered. Opening a dialog to get user input")

        textEntryDialog = wx.TextEntryDialog(self, "Please enter a URL to a jpg or png image for the album artwork.",
                                             caption="Enter URL")
        if textEntryDialog.ShowModal() != wx.ID_CANCEL:
            self.worker(self.changeAAThread, (textEntryDialog.GetValue(),), {})
            self.logger.info("Album artwork location changed. New album artwork location is: {}".format(
                textEntryDialog.GetValue()))
        else:
            self.logger.info("Choose album artwork (URL) event canceled.")

    def onChooseAAThumb(self, event):
        """
        Changes the album artwork to that of the video's thumbnail.
        """

        self.logger.info("Choose album artwork (thumb) event triggered. Changing album artwork to the thumbnail")
        self.worker(self.changeAAThread, (self.YTSong.thumb, ), {})

    def onChooseDownloadPath(self, event):
        """
        Opens up a dialog allowing the user to choose their own download path.
        """

        self.logger.info("Choose download path event triggered. Opening a dialog for user input now.")

        dirDialog = wx.DirDialog(self, "Please choose a folder in which to download the file into.")
        if dirDialog.ShowModal() != wx.ID_CANCEL:
            self.downloadPath = dirDialog.GetPath()
            self.tempDownloadPath = self.downloadPath
            self.radioDownload.SetValue(False)
            self.radioIT.SetValue(False)
            self.logger.info("Download path changed. New download path is: {} and new temp download path is: {}".format(
                self.downloadPath, self.tempDownloadPath))
            self.updateDownloadLabel()
        else:
            self.logger.info("Choose download path event canceled.")

    def onChangeDownLociTunes(self, event):
        """
        Changes self.downloadPath to Liber.ITUNES and changes self.tempDownloadPath to Liber.ITUNES_TEMP
        """

        self.logger.info("Download to iTunes radio button triggered. Changing download path to Liber.ITUNES and "
                         "changing temp download path to Liber.ITUNES_TEMP")
        self.downloadPath = Liber.ITUNES
        self.tempDownloadPath = Liber.ITUNES_TEMP
        self.updateDownloadLabel()

    def onChangeDownLocDownloads(self, event):
        """
        Changes self.downloadPath and self.tempDownloadPath to Liber.DOWNLOADS
        """

        self.logger.info("Download to downloads radio button triggered. Changing download path to Liber.DOWNLOADS "
                         "and changing temp download path to Liber.DOWNLOADS")
        self.downloadPath = Liber.DOWNLOADS
        self.tempDownloadPath = self.downloadPath
        self.updateDownloadLabel()

    def onChangeDownloadType(self, event):
        """
        Logs the event of the user changing the download type and updates self.downloadType based on the values of
        self.radioAudio and self.radioVideo. Also disable all elements of the GUI that cannot be used with the
        associated download type.
        :return: None
        """

        if self.radioAudio.GetValue() is True:
            self.downloadType = Liber.ID_AUDIO
            for x, y in self.metadata.items():
                y[1].Enable()
            self.btAAPath.Enable()
            self.btAAThumb.Enable()
            self.btAAURL.Enable()
        elif self.radioVideo.GetValue() is True:
            self.downloadType = Liber.ID_VIDEO
            for x, y in self.metadata.items():
                if x != 'title':
                    y[1].Disable()
            self.btAAPath.Disable()
            self.btAAThumb.Disable()
            self.btAAURL.Disable()

        self.logger.info("Download type has been changed to {} (Liber.ID_AUDIO: {}, Liber.ID_VIDEO: {})".format(
            self.downloadType, self.downloadType == Liber.ID_AUDIO, self.downloadType == Liber.ID_VIDEO))

    def onUpdatePB(self, event):
        """
        Updates the progress bar using the given ratio found in event.GetValue(). Since we are tracking two ratios
        that return how much they are complete out of 100, we have to split the progress bar into two.
        """

        if self.downloadType == Liber.ID_AUDIO:
            if self.progressBar.GetValue() >= 50:
                value = 50 + event.GetValue() * 50
            else:
                value = event.GetValue() * 50
        elif self.downloadType == Liber.ID_VIDEO:
            value = event.GetValue() * 100
        else:
            value = 100
            self.logger.warning("Invalid download type. Cannot update progress bar! Setting value to 100.")

        self.progressBar.SetValue(value)

        if self.progressBar.GetValue() >= 100:
            self.updateDownloadLabel("Finished")
            self.enableDownloads = True
            self.worker(self.resetPBandDBThread, (), {})

    def callbackDownload(self, total, recvd, ratio, rate, eta):
        """
        Changes the progress bar based on download ratio. In order to do this the EVT_CHANGE_SB is raised
        :param total: Total download size (bytes)
        :param recvd: Total amount downloaded (bytes)
        :param ratio: Percentage downloaded
        :param rate: Rate of download
        :param eta: Estimated Time until Arrival of song
        """

        evt = UpdateProgressBarEvent(myEVT_UPDATE_PROGRESSBAR, -1, ratio)
        wx.PostEvent(self, evt)

    def callbackMetadata(self, ratio):
        """
        While metadata is being added in the Liber module, this funciton is called to show progress.
        :param ratio: 0<x<1, percentage of completion for adding the metadata
        """

        evt = UpdateProgressBarEvent(myEVT_UPDATE_PROGRESSBAR, -1, ratio)
        wx.PostEvent(self, evt)

    def download(self, evt):
        """
        Calls the paired YTSong method download, using self.callback to change the progress bar and threading.
        """

        self.logger.info("Download method invoked. Downloading now.")

        if self.downloadPath is not None and self.tempDownloadPath is not None and self.enableDownloads is True:
            self.btDownload.Disable()
            self.updateDownloadLabel("Downloading...")
            self.btDownload.Fit()
            self.enableDownloads = False
            self.progressBar.SetValue(0)
            metadata = {}
            for x, y in Liber.METADATA.items():
                metadata[x] = self.metadata[x][1].GetValue()
            self.worker(self.YTSong.download, (self.downloadPath, self.tempDownloadPath),
                        {"downloadType": self.downloadType, "metadata": metadata, "album_artwork": self.artworkSource,
                         "callbackDown": self.callbackDownload, "callbackMetadata": self.callbackMetadata})

        elif self.enableDownloads is False:
            self.logger.info("Unable to download: it has been disabled.")
        else:
            self.logger.error("Unable to download: None of the radio buttons have been pressed- no "
                              "download location set!")


class MainFrame(wx.Frame):
    """
    This is the GUI structure that holds all the tiles in a scrollable window. Contains a download-all button, an
    add new tile button, and the about and help menus.
    """

    def __init__(self, parent, *args, **kwargs):
        """
        Create the frame and ask for the first URL.
        """

        self.logger = logger.getChild("MainFrame")
        self.logger.info("Constructing")

        super(MainFrame, self).__init__(parent, *args, **kwargs)
        self.SetSize(TILE_SIZE)
        self.tiles = []

        # add an icon and a title
        if platform.system() == 'Windows':
            self.SetIcon(wx.Icon(os.getcwd()+'\docs\\256x256.png',
                                 wx.BITMAP_TYPE_ANY))
        else:
            self.SetIcon(wx.Icon(os.getcwd()+'/docs/256x256.png',
                                 wx.BITMAP_TYPE_ANY))
        self.SetTitle("Liber")

        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()
        fileAbout = fileMenu.Append(wx.ID_ABOUT, 'About', 'Show information about this application')
        self.Bind(wx.EVT_MENU, self.onAbout, fileAbout)
        fileExit = fileMenu.Append(wx.ID_EXIT, 'Exit', 'Exit application')
        self.Bind(wx.EVT_MENU, self.onClose, fileExit)
        menuBar.Append(fileMenu, '&File')
        self.SetMenuBar(menuBar)

        self.scrollPanel = scrolled.ScrolledPanel(self, size=(TILE_SIZE[0] + 50, TILE_SIZE[1]))
        self.scrollPanelvSizer = wx.BoxSizer(wx.VERTICAL)
        self.scrollPanel.SetSizer(self.scrollPanelvSizer)
        self.scrollPanel.SetAutoLayout(1)
        self.scrollPanel.SetupScrolling(50, 50, 0)

        self.controlPanel = wx.Panel(self, size=(TILE_SIZE[0], -1))
        self.controlPanel.SetBackgroundColour("#ff3333")
        self.btDownloadAll = wx.Button(self.controlPanel, wx.ID_ANY, "Download all")
        self.Bind(wx.EVT_BUTTON, self.onDownloadAll, self.btDownloadAll)
        self.btAddTile = wx.Button(self.controlPanel, wx.ID_ANY, "Add video")
        self.Bind(wx.EVT_BUTTON, self.onAddTile, self.btAddTile)
        self.btExit = wx.Button(self.controlPanel, wx.ID_ANY, "Exit")
        self.Bind(wx.EVT_BUTTON, self.onClose, self.btExit)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        vSizer = self.getControlPanelSizer()
        self.controlPanel.SetSizerAndFit(vSizer)

        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mainSizer.Add(self.controlPanel, flag=wx.EXPAND | wx.ALIGN_LEFT)
        self.mainSizer.Add(self.scrollPanel, flag=wx.EXPAND)
        self.SetSizer(self.mainSizer)

        self.onAddTile(None)
        self.Fit()
        self.Show()

    def onAbout(self, event):
        """
        Displays an about dialog
        """

        description = """Liber is an application that is meant to help others download YouTube videos
with ease of use, for it puts all the steps into one location (such as: adding information to the audio,
adding album artwork to the audio, adding the audio/video into iTunes, etc.). That being said, Liber's intent is
for downloading NON-COPYRIGHTED music/content, for doing so is illegal. Also, watching YouTube videos without
streaming them is a violation of YouTube's end user agreement, so use at your own risk
(see http://www.pcadvisor.co.uk/how-to/internet/is-it-legal-download-youtube-videos-3420353/ for more
info). If you would like to report a bug or contribute to this open-source project, see:
https://github.com/DevelopForLizardz/Liber"""

        licence = """Liber is free software and can be used, modified and distributed, however only done so under the
terms and conditions of the MIT License (which can be found here: https://opensource.org/licenses/MIT). Liber
is also distributed without any warranty."""

        info = wx.AboutDialogInfo()
        info.SetIcon(wx.Icon(os.path.dirname(__file__)+'/docs/512x512.png', wx.BITMAP_TYPE_ANY))
        info.SetName("Liber")
        info.SetVersion(str(__version__))
        info.SetDescription(description)
        info.SetCopyright('(C) 2015 Ryan Drew')
        info.SetLicense(licence)
        info.AddDeveloper("Ryan Drew")
        info.AddArtist("Grace Drew")

        wx.AboutBox(info)

    def getControlPanelSizer(self):
        """
        Returns a horizontal box sizer that contains the elements for the control panel area on the left side.
        This allows for that area to be resized easily when the size of the window changes
        """

        controlEndPadding = (-1, (self.GetSize()[1] - (10 + self.btDownloadAll.GetSize()[1] +
                                                       self.btAddTile.GetSize()[1] + self.btExit.GetSize()[1])) / 4.0)
        hSizer = wx.BoxSizer(wx.VERTICAL)
        hSizer.Add(controlEndPadding)
        hSizer.Add(self.btDownloadAll, flag=wx.CENTER)
        hSizer.Add(controlEndPadding)
        hSizer.Add(self.btAddTile, flag=wx.CENTER)
        hSizer.Add(controlEndPadding)
        hSizer.Add(self.btExit, flag=wx.CENTER)
        hSizer.Add(controlEndPadding)
        return hSizer

    def onDownloadAll(self, event):
        """
        Sends a message to each tile telling them to start downloading.
        """

        for x in self.tiles:
            x.download(None)

    def onAddTile(self, event):
        """
        Obtains a YouTube URL from the user and creates a tile for it, adding the tile into self.tiles. If obtaining
        the video fails, an error message dialog pops up, telling the user of the error, where they can report the
        error, and whether they want to continue using the program or quit.
        """

        textEntryDialog = wx.TextEntryDialog(self, "Please enter the URL for a YouTube video you wish to download",
                                             "Enter a YouTube URL",
                                             defaultValue="https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        if textEntryDialog.ShowModal() != wx.ID_CANCEL:
            try:
                self.tiles.append(Tile(textEntryDialog.GetValue(), self.scrollPanel, parentLogger=self.logger))
                self.SetMaxSize((-1, -1))
                if len(self.tiles) > 1:
                    self.scrollPanelvSizer.Add((-1, 10))
                    self.scrollPanelvSizer.Add((wx.StaticLine(self.scrollPanel, size=(TILE_SIZE[0], -1))))
                    self.scrollPanelvSizer.Add((-1, 10))
                self.scrollPanelvSizer.Add(self.tiles[len(self.tiles) - 1])
                self.scrollPanel.SetSizer(self.scrollPanelvSizer)
                w, h = self.scrollPanelvSizer.GetMinSize()
                self.scrollPanel.SetVirtualSize((w, h))
                self.scrollPanel.AdjustScrollbars()

                if self.GetSize()[1] < wx.DisplaySize()[1] / 2.0:
                    self.SetSize((TILE_SIZE[0]+self.controlPanel.GetSize()[0]+10, len(self.tiles) * (TILE_SIZE[1]+20)))
                    self.controlPanel.SetSizerAndFit(self.getControlPanelSizer())
                    self.SetMinSize(self.GetSize())
                    self.SetMaxSize(self.GetSize())
                else:
                    self.SetMaxSize(self.GetSize())
                    self.scrollPanel.Scroll(0, self.GetSize()[1])

                self.Refresh()

            except Exception, e:
                self.logger.error("An error occured while trying to create a tile", exc_info=True)
                messageDialog = wx.MessageDialog(self,
                                                 "An error occured while trying to fetch your video: {}. Sorry "
                                                 "about that. To report this issue, visit: {}".format(
                                                        e, "https://github.com/DevelopForLizardz/Liber"),
                                                 style=wx.CANCEL | wx.ICON_ERROR)
                messageDialog.ShowModal()

        elif len(self.tiles) == 0:
            self.logger.info("User pressed cancel to first 'add video' prompt. Destroying.")
            self.Destroy()
            self.DestroyChildren()
            sys.exit(0)

    def onClose(self, event):
        """
        Pops up a dialog asking the user if they are sure that they want to quit. Then quits the program based
        on user input
        """

        self.logger.info("Close event triggered. Asking for confirmation from user.")

        quitDialog = wx.MessageDialog(self, "Are you sure you want to quit?", "Exit",
                                      style=wx.OK | wx.CANCEL | wx.ICON_HAND)
        if quitDialog.ShowModal() == wx.ID_OK:
            self.logger.info("Destroying")
            self.Destroy()
            self.DestroyChildren()
            sys.exit(0)
        else:
            self.logger.info("Close event canceled")


if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame(None)
    frame.Show()
    frame.Center()
    app.MainLoop()
