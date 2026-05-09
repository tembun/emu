#!/usr/bin/env python3

#
# emn -- email notifier.
#
# The main configuration file for the program is $HOME/.emnrc (it can be
# overriden by the first optional argument), which should define the
# following variables, using the syntax:
#   "%s = %s", variable_name, variable_value
# pass      A filepath to the private configuration file (see below).
# notifier  A command that will be used for sending notification.
#           The '{FROM}' substring will be replaced with the sender address.
# interval  Interval in second, in which the program will re-check the inbox.
# $HOME in the variable name will be replaced with the user's home directory.
#
# The private (pass-) configuration file is used to store credentials for
# accessing the mail inbox. This file should have the following variables set
# using the following syntax:
#   "%s %s", variable_name variable_value
# serv      The IMAP server.
# login     Login at the IMAP server.
# password  Password for the login.
#

from email.header import decode_header, make_header
from functools import reduce
import email
import imaplib
import os
import sys
import time

HOME = os.getenv('HOME')
# First argument may specify a path to an alternate configuration file.
if (len(sys.argv) == 2):
    config_path = sys.argv[1]
else:
    config_path = f"{HOME or '.'}/.emnrc"
progname = os.path.basename(sys.argv[0]).removesuffix('.py')

config = {
        'pass': {
            'name': 'pass',
        },
        'server': {
            'name': 'serv',
            'private': True,
        },
        'login': {
            'name': 'login',
            'private': True,
        },
        'password': {
            'name': 'password',
            'private': True,
        },
        'notifier': {
            'name': 'notifier'
        },
        'interval': {
            'name': 'interval',
            'value': 30,
        },
}

def warn(*args, **kwargs):
    print('%s: %s' % (progname, *args), file=sys.stderr, **kwargs)

def err(*args, **kwargs):
    warn(*args, **kwargs)
    sys.exit(1)

def get_var(var):
    return config[var]['value']

def process_config():
    try:
        with open(config_path, 'r') as f:
            lines = f.read().split('\n')
            lines = [l for l in lines if l]
    except:
        err(f'Config file not found: {config_path}')
    vars = [l.split(' = ') for l in lines]
    vars = { a[0]: a[1] for a in vars }
    for prop in config:
        data = config[prop]
        if data.get('private'):
            continue
        var_val_raw = vars.get(data['name'])
        if var_val_raw:
            var_val = var_val_raw.replace('$HOME', HOME)
            data['value'] = var_val
        elif not data.get('value'):
            err(f"Config variable is not set: {data['name']}")

    try:
        with open(get_var('pass'), 'r') as f:
            lines = f.read().split('\n')
            lines = [l for l in lines if l]
    except:
        err(f"Pass-config file not found: {get_var('pass')}")
    vars = [l.split(' ', 1) for l in lines]
    vars = {a[0]: a[1] for a in vars }
    for prop in config:
        data = config[prop]
        if not data.get('private'):
            continue
        var_val = vars.get(data['name'])
        if not var_val:
            err(f"Private-config variable is not set: {data['name']}")
        data['value'] = var_val

def check_and_notify():
    while True:
        try:
            mail.noop()
            break
        except:
            DELAY = 5
            warn(f"Can not connect to the server: {get_var('server')}."
                 f' Retry after {DELAY} seconds')
            try:
                time.sleep(DELAY)
            except:
                exit(0)
    status, data = mail.search(None, 'UNFLAGGED')
    mail_ids = reduce(lambda acc, block: acc + block.split(), data, [])
    for mail_id in mail_ids:
        status, data = mail.fetch(mail_id, 'BODY[HEADER]')
        for response_part in data:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1])
                sender = make_header(decode_header(message['from']))
                mail.store(mail_id, '-FLAGS', r'\SEEN')
                mail.store(mail_id, '+FLAGS', r'\Flagged')
                notifier_cmd = get_var('notifier').replace('{FROM}', str(sender))
                os.system(notifier_cmd)

process_config()
while True:
    try:
        mail = imaplib.IMAP4_SSL(get_var('server'))
        break
    except:
        DELAY = 5
        warn(f"Can not connect to the server: {get_var('server')}."
             f' Retry after {DELAY} seconds')
        try:
            time.sleep(DELAY)
        except:
            exit(0)
mail.login(get_var('login'), get_var('password'))
mail.select('inbox')

while True:
    check_and_notify()
    try:
        time.sleep(int(get_var('interval')))
    except:
        sys.exit(0)
