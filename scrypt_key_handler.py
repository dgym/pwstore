from base64 import b64encode, b64decode
from Crypto import Random

import scrypt

from key_handler import PassphraseKeyHandler
from option import Option


class ScryptKeyHandler(PassphraseKeyHandler):
    name = 'scrypt'
    options = [
        Option('time',
               'seconds to spend deriving key',
               check='\\d+',
               converter=int),
    ]

    data = None

    def make_key(self, key_len, options):
        self.key = Random.new().read(key_len)
        self.data = b64encode(scrypt.encrypt(
            self.key,
            self.passphrase,
            maxtime=options['time'])
        )

    def store(self):
        return self.data

    def load(self, _key_len, data):
        self.data = data
        try:
            self.key = scrypt.decrypt(
                b64decode(self.data),
                self.passphrase,
            )
            return True
        except scrypt.error:
            return False
