# Description

Script for automatic accounts registration and configs downloading in russian VPN service (free first 24-hours, than need to rerun). Script handling registration,
captcha recognition (ImageMagic + tesseract-ocr), email confirmation, logging in,
downloading configs and starting openvpn automatically.

Just for fun.

# Requirements

* python3.5
* tesseract-ocr 4 (from https://launchpad.net/~alex-p/+archive/ubuntu/tesseract-ocr) or the old one (but remove '--oem 0' flags in the main.py)
* ImageMagick
* openvpn
* packages:
    * requests
    * bs4
    * lxml

# Usage

``` python3 main.py ```