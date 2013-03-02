from base64 import b64encode, b64decode
import hashlib
import ctypes

from Crypto import Random


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


class Pbkdf2KeyHandler(object):
    name = 'pbkdf2'
    iterations = 20000
    
    def __init__(self):
        super(Pbkdf2KeyHandler, self).__init__()
        self.key = None
        self.salt = None

    def make_key(self, passphrase, key_len):
        self.salt = Random.new().read(64)
        self.key = pbkdf2_hmac_sha512(
            passphrase,
            self.salt,
            self.iterations,
            key_len,
        )

    def store(self):
        return {
            'salt': b64encode(self.salt),
            'iterations': self.iterations,
        }

    def load(self, key_len, passphrase, data):
        self.salt = b64decode(data['salt'])
        self.iterations = data['iterations']
        self.key = pbkdf2_hmac_sha512(
            passphrase,
            self.salt,
            self.iterations,
            key_len,
        )
