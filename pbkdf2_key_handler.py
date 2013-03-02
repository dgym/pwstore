from base64 import b64encode, b64decode
import hmac
import hashlib
from struct import Struct

from Crypto import Random


try:
    import ctypes
    SSL = ctypes.cdll.LoadLibrary('libssl.so')
except ImportError:
    SSL = False
except OSError:
    SSL = False


if SSL:
    # pylint: disable=E1103
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
else:
    # pylint: disable=E1101
    def pbkdf2_hmac_sha512(key, salt, iterations, keylen):
        mac = hmac.new(key, None, hashlib.sha512)
        inner = mac.inner
        outer = mac.outer
        
        def pseudorandom(data):
            i = inner.copy()
            i.update(data)
            o = outer.copy()
            o.update(i.digest())
            return o.digest()
        
        pack_int = Struct('>I').pack

        result = ''
        for block in xrange(1, -(-keylen//mac.digest_size)+1):
            u = pseudorandom(salt+pack_int(block))
            rv = bytearray(u)
            for _ in xrange(iterations-1):
                u = pseudorandom(u)
                for j in xrange(len(rv)):
                    rv[j] ^= ord(u[j])
            result += str(rv)
        return result[:keylen]


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
