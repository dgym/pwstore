import re
import json
from base64 import b64encode, b64decode
from getpass import getpass
import readline
from hashlib import sha512
from collections import OrderedDict

from Crypto.Cipher import AES, Blowfish
from pbkdf2_key_handler import Pbkdf2KeyHandler
from stage import Stage


CIPHERS = {
    'aes': AES,
    'blowfish': Blowfish,
}


KEY_HANDLERS = {
    'pbkdf2': Pbkdf2KeyHandler,
}


class Store(object):
    def __init__(self):
        self.stages = []
        self.key = None
        self.entries = {}

    def load(self, filename):
        with open(filename, 'r') as stream:
            contents = stream.read()
        contents = json.loads(contents)

        passphrase = self.get_passphrase()
        self.stages = []
        for idx, parameters in enumerate(contents['stages'], 1):
            cipher_name = parameters['cipher']
            cipher = CIPHERS[cipher_name]
            key_handler = KEY_HANDLERS[parameters['key_handler']]()
            key_handler.load(
                cipher.key_size[-1],
                passphrase,
                parameters['key_data'],
            )
            self.stages.append(Stage(cipher_name, cipher, key_handler))

        ciphertext = b64decode(contents['ciphertext'])
        for stage in reversed(self.stages):
            ciphertext = stage.decrypt(ciphertext)

        match = re.match(r'check:(\d+):([^:]+):(.*)', ciphertext)
        if not match:
            raise ValueError('Bad passphrase used, decrypt failed')
        length = int(match.group(1))
        digest = match.group(2)
        plaintext = match.group(3)[:length]
        if not digest == sha512(plaintext).hexdigest():
            raise ValueError('Bad passphrase used, decrypt failed')
        self.entries = json.loads(plaintext)

    def create(self):
        self.stages = []
        passphrase = self.get_passphrase(confirm=True)

        key_handler = Pbkdf2KeyHandler()
        key_handler.make_key(passphrase, AES.key_size[-1])
        self.stages.append(Stage('aes', AES, key_handler))

        key_handler = Pbkdf2KeyHandler()
        key_handler.make_key(passphrase, Blowfish.key_size[-1])
        self.stages.append(Stage('blowfish', Blowfish, key_handler))

    def save(self, filename):
        plaintext = json.dumps(self.entries)
        plaintext = 'check:%i:%s:%s' % (
            len(plaintext),
            sha512(plaintext).hexdigest(),
            plaintext,
        )
        ciphertext = plaintext
        for stage in self.stages:
            ciphertext = stage.encrypt(ciphertext)
        contents = json.dumps(
            OrderedDict([
                ('stages', [stage.to_dict() for stage in self.stages]),
                ('ciphertext', b64encode(ciphertext)),
            ]),
            indent=4,
            separators=(', ', ': '),
        )
        with open(filename, 'w') as stream:
            stream.write(contents + '\n')

    def get_passphrase(self, confirm=False):
        while True:
            passphrase = getpass("Passphrase: ")
            if not passphrase:
                continue

            if confirm:
                again = getpass("Confirm passphrase: ")
                if passphrase != again:
                    print 'Passphrases did not match, please try again.'
                    continue

            break
        return passphrase
