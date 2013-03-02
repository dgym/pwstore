KEY_HANDLERS = {}


class KeyHandlerMeta(type):
    def __init__(mcs, name, bases, dct):
        super(KeyHandlerMeta, mcs).__init__(name, bases, dct)
        if dct.get('name'):
            KEY_HANDLERS[dct['name']] = mcs


class KeyHandler(object):
    __metaclass__ = KeyHandlerMeta

    options = []

    key = None

    def make_key(self, _key_len, _options):
        pass

    def store(self):
        return {}

    def load(self, _key_len, _data):
        return False


class PassphraseKeyHandler(KeyHandler):
    def __init__(self):
        super(PassphraseKeyHandler, self).__init__()
        self.passphrase = None


# pylint: disable=W0611
import scrypt_key_handler
import pbkdf2_key_handler
