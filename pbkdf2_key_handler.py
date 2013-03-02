from base64 import b64encode, b64decode
import hashlib
import ctypes

from Crypto import Random

from key_handler import PassphraseKeyHandler
from option import Option


SSL = ctypes.cdll.LoadLibrary('libssl.so')


def pbkdf2_hmac_sha512(key, salt, iterations, keylen):
    SSL.EVP_sha512.restype = ctypes.c_void_p
    evp = ctypes.cast(SSL.EVP_sha512(), ctypes.POINTER(ctypes.c_void_p))
    result = ctypes.create_string_buffer('', size=keylen)
    SSL.PKCS5_PBKDF2_HMAC(
        key, len(key),
        salt, len(salt),
        int(iterations),
        evp,
        keylen,
        ctypes.byref(result)
    )
    return result.raw


class Pbkdf2KeyHandler(PassphraseKeyHandler):
    name = 'pbkdf2'
    options = [
        Option('iterations',
               'at least 10,000',
               check='\\d+',
               converter=int),
    ]

    salt = None
    iterations = None

    def make_key(self, key_len, options):
        self.salt = Random.new().read(64)
        self.iterations = options['iterations']
        self.key = pbkdf2_hmac_sha512(
            self.passphrase,
            self.salt,
            self.iterations,
            key_len,
        )

    def store(self):
        return {
            'salt': b64encode(self.salt),
            'iterations': self.iterations,
            'hash': hashlib.sha512(self.key).hexdigest(),
        }

    def load(self, key_len, data):
        self.salt = b64decode(data['salt'])
        self.iterations = data['iterations']
        self.key = pbkdf2_hmac_sha512(
            self.passphrase,
            self.salt,
            self.iterations,
            key_len,
        )
        return hashlib.sha512(self.key).hexdigest() == data['hash']
