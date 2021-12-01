This is a simple (quick & dirty) Kino DV to Kdenlive file converter.

Requires Python 3.

Notes:

* **Currently hardcoded for PAL DV**.

* rewrites file paths relative to the current directory if
  it finds a similarly named file there, which may be wrong.
  You may have to fix this by hand.

Usage:

`kino-kdenlive.py example.kino`

Will write a example.kdenlive file with:

* a main bin including all media
* audio and video timelines corresponding to the Kino file
* grouped audio and video cuts

Enjoy!

Pierre
