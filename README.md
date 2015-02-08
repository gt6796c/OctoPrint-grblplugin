OctoPrint grbl Plugin 
=========================

Largely inspired by https://github.com/PxT/OctoPrint.git except targeted at OctoPrint v1.2 (the devel branch.)

This currently works against a modified version of the OctoPrint devel branch at https://github.com/gt6796c/OctoPrint.git (the octogrbl branch.) This branch adds more hooks into OctoPrint's comm channels. I tried to keep the changes as minimal and localized as possible to facilitate keeping in line with the main branch.

Usage:
Create a Printer Profile and ensure that the model name of the printer has the string "(grbl)" in it. 
This activates the plugin which will intercept and inject commands as necessary to successfully communicate with a grbl v0.9 board (at least it does for me on my ShapeOko2.)


