# Description

Script for automatic accounts registration and configs downloading in russian VPN service (free first 24-hours, than need to rerun). Script handling registration,
captcha recognition (ImageMagic + tesseract-ocr), email confirmation, logging in,
downloading configs and starting openvpn automatically.

Just for fun.

# Requirements

* python3.5
* tesseract
* ImageMagick
* openvpn
* packages:
    * requests
    * BeautifulSoup
    * lxml

# Usage

``` python3 main.py ```