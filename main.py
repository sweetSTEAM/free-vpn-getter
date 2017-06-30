import string
import random
import subprocess
import requests
import time
import hashlib
import os
import re
import zipfile
from PIL import Image
from bs4 import BeautifulSoup


REG_VIEW_URL = 'https://vpnsafe.ru/component/users/?view=registration'
REG_POST_URL = 'https://vpnsafe.ru/component/users/?task=registration.register'
LOG_POST_URL = 'https://vpnsafe.ru/'
CAPTCHA_PLUGIN_URL = ('https://vpnsafe.ru/plugins/captcha/n3tseznamcaptcha/'
                        'captcha.create.php')
CAPTCHA_SERVICE_URL = 'https://captcha.seznam.cz/captcha.getImage'
NAME_LEN = 8
MAIL_DOM_URL = 'http://api.temp-mail.ru/request/domains/format/json/'
MAIL_EMAILS_URL = 'http://api.temp-mail.ru/request/mail/id/'

# Requesting the list of tempmail domains
doms_r = requests.get(MAIL_DOM_URL)
doms_r.raise_for_status()
doms = doms_r.json()

session = requests.Session()
# Requesting the registration view 
reg_view = session.get(REG_VIEW_URL)
reg_view.raise_for_status()
html = BeautifulSoup(reg_view.content, 'lxml')

# Genereting registration data
name = ''.join(random.choice(string.ascii_lowercase + string.digits)
                for _ in range(NAME_LEN))
password = name # just kek
email = name + random.choice(doms)
some_id = html.find('form', id='member-registration').find('input',
    attrs={'value': '1'})['name']

# Trying to solve captcha
print("Solving captcha...\n")
do = True
while do:
    try:
        # Getting captcha hash from plugin on target service
        r = requests.get(CAPTCHA_PLUGIN_URL)
        r.raise_for_status()
        captcha_hash = r.text

        # Captcha image getting from captcha service
        c = requests.get(CAPTCHA_SERVICE_URL, params = {'hash': captcha_hash})
        c.raise_for_status()
        captcha_file = captcha_hash + '.png'
        with open(captcha_file, 'wb') as f:
            f.write(c.content)

        # Raw captcha couldn't be solved because it has background abberations 
        # But after some photoshop magic :3 backround disappears!
        try:
            params_conv = ['convert', captcha_file, '-paint', '1.1',
                '-monochrome', captcha_file]
            subprocess.check_call(params_conv)
        except Exception as e:
            os.remove(captcha_file)
            raise e

        # Captcha SOLVING
        captcha_out = captcha_hash
        params_solve = ['tesseract', captcha_file,
                        '--oem', '0', '-l', 'eng', captcha_out]
        subprocess.check_call(params_solve)
        captcha_text = open(captcha_out + '.txt', 'r').readline().strip()

        if len(captcha_text) != 5:
            os.remove(captcha_file), os.remove(captcha_out + '.txt')
            raise Exception('Wrong format of captcha: ' + captcha_text)

        # Clean up
        os.remove(captcha_file), os.remove(captcha_out + '.txt')

        # Registration form
        payload = {
            'jform[name]': name,
            'jform[username]': name,
            'jform[password1]': password,
            'jform[password2]': password,
            'jform[email1]': email,
            'jform[email2]': email,
            'jform[captcha_hash]': captcha_hash,
            'jform[captcha]': captcha_text.upper(),
            'option': 'com_users',
            'task': 'registration.register',
            some_id: 1
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Chrome/58.0.3029.110'}
        # Registration request
        reg_post = session.post(REG_POST_URL, data=payload, headers=headers)
        reg_post.raise_for_status()
        # Cheking captcha corectness
        if (reg_post.history[0].headers['Location']
            == '/component/users/?view=registration'):
            raise Exception(captcha_text.upper() + ' '
                + BeautifulSoup(reg_post.content, 'lxml').find(
                    'div', 'alert-message').text) 
        else:
            do = False
            print("CAPTCHA SOLVED:", captcha_text.upper())
            break
    except Exception as e:
        # print(repr(e))
        pass

print("\nLOGIN INFO:")
print('LOGIN (and PASS):', name), print("EMAIL:", email)

# Checking conformation email
do = True
while do:
    try:
        time.sleep(1)

        # Tempmail API requires md5 hash of the email string as id
        md5 = hashlib.md5()
        md5.update(email.encode('utf-8'))
        md5 = md5.hexdigest()

        # Requesting the list of emails
        emails = requests.get(MAIL_EMAILS_URL + md5 +'/format/json')
        emails.raise_for_status()
        emails = emails.json()
        if 'error' in emails:
            raise Exception(emails['error'])

        email = emails[0]
        if 'vpnsafe.net' not in email['mail_from']:
            raise Exception("Email not found")
        text = email['mail_text']

        do = False
        break
    except Exception as e:
        print(repr(e))
        # pass

# Retriving url for account activation from email text
activation_url = re.search("(?P<url>https?://[^\s]+)", text).group("url")
activ = session.get(activation_url)
activ.raise_for_status()
print("Account activated")

# Logging in
html = BeautifulSoup(activ.content, 'lxml')
some_id2 = html.find('form', id='login-form').find('input',
    attrs={'name': 'return'})['value']
payload = {
    'username': name,
    'password': password,
    'Submit': '',
    'option': 'com_users',
    'task': 'user.login',
    'return': some_id2,
    some_id: 1
}
log_post = session.post(LOG_POST_URL, data=payload, headers=headers)
log_post.raise_for_status()

print("Logged in, downloading config...")
# Downloading config zip
payload = {
    'cmd': 'download_cert'    
}
configs = session.post(LOG_POST_URL, data=payload, headers=headers)
d = configs.headers['content-disposition']
cfg_filename = re.search("filename=(.+)", d).group(1)
with open(cfg_filename, 'wb') as f:
    f.write(configs.content)

# Unzipping
zip_ref = zipfile.ZipFile(cfg_filename, 'r')
zip_ref.extractall(name)
zip_ref.close()
print("Config downloaded and unpacked: ./", name, sep="")
os.remove(cfg_filename)
os.chdir(name)

# Appending additional google DNS settings
appends = [
    'dhcp-option DNS 8.8.8.8',
    'script-security 2',
    'up /etc/openvpn/update-resolv-conf',
    'down /etc/openvpn/update-resolv-conf'
]
for filename in os.listdir():
    if filename.endswith(".ovpn"):
        with open(filename, "a") as file:
            for a in appends:
                print(a, file=file)

# Connecting
cfg = 'VPNSafe.ru Netherlands, Amsterdam UDP(53).ovpn'
params_vpn = ['sudo', 'openvpn', '--config', cfg]
print("Stating openvpn... " + " ".join(params_vpn))
p = subprocess.run(params_vpn)
