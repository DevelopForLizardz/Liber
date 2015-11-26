# Liber
GUI application for downloading YouTube videos.  

## About

This project is being used as a learning project, to get experience in the creation, distribution and managagment of applications/programs. 
It is meant to be used in the form of the executables (found under [Liber/dist](https://github.com/DevelopForLizardz/Liber/blob/master/Liber/dist/Liber.app.zip)), however using the source code in a project of your own is also encouraged.

## Download/Installation

**OSX:**

Download Liber.app.zipp found under [Liber/dist](https://github.com/DevelopForLizardz/Liber/blob/master/Liber/dist/Liber.app.zip), uncompress it, and then put it into your Applications folder.

**Windows:**

(coming soon- testing needed)

**Linux:**

Download the [source code](https://github.com/DevelopForLizardz/Liber/tree/master/Liber) (folders dist and build not needed) and run setup.py to install dependencies, however one of the dependencies also requires [ffmpeg](http://www.ffmpeg.org). To install, execute:

```bash
sudo apt-get install ffmpeg
```

(If you are using Ubuntu 14.04, you might need to run ```bash add-apt-repository ppa:mc3man/trusty-media && sudo apt-get update && sudo apt-get dist-upgrade``` first.)

## Dependencies (if using a Linux distribution or as a module)

[**Python 2.7**](http://python.org) (support for Python 3.5 coming soon)

[**Pafy**](http://np1.github.io/pafy/)- Used for communication with YouTube

[**PyDub**](https://github.com/jiaaro/pydub)- Used to convert audio files to mp3 and to add metadata

[**mutagen**](https://bitbucket.org/lazka/mutagen)- Used to add album artwork to audio

[**youtube-dl**](http://rg3.github.io/youtube-dl/)- Dependency for Pafy.

[**ffmpeg**](http://www.ffmpeg.org)- Dependency for PyDub

## License ([MIT License](http://opensource.org/licenses/mit-license.php))

The MIT License (MIT)

Copyright (c) 2015 Ryan Drew

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
