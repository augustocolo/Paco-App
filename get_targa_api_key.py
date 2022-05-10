import time

import requests

import random
import string

import pydispo

letters = string.ascii_lowercase
username = ''.join(random.choice(letters) for i in range(10))

url = 'https://www.regcheck.org.uk/ajax/register.aspx'

email = pydispo.generate_email_address()

res = requests.post(url, data={
    'tbUsername': username,
    'tbPassword': username,
    'ddlLanguage': 'Python',
    'tbEmail': email,
    'intAffiliate': 0
})

print(res.status_code)
print(res.text)

time.sleep(30)

pydispo.check_mailbox(email)