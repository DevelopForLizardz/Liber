# Liber
GUI application for downloading YouTube videos.  

(C) Ryan Drew 2015

Executables will be added shortly, but for now (in order to use), download the source code found above and launch 
__setup.py__ first, and then __main.py__.

Liber requires these packages:

__Pafy__

__Pydub__ 

__mutagen__

__youtube-dl__

and __ffmpeg__

All of these, except __ffmpeg__ can be installed using __Pip__ and will be installed during the execution of __setup.py__. __Ffmpeg__, on the other hand, can be installed by using __apt-get install ffmpeg__,
however if you are using Ubuntu 14.04, you might need to execute __sudo add-apt-repository ppa:mc3man/trusty-media && sudo apt-get update && sudo apt-get dist-upgrade__ first, in order to give apt a source.
