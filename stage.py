from Crypto import Random


class Stage(object):
    def __init__(self, cipher_name, cipher, key_handler):
        self.cipher_name = cipher_name
        self.cipher = cipher
        self.key_handler = key_handler

    def to_dict(self):
        return {
            'cipher': self.cipher_name,
            'key_handler': self.key_handler.name,
            'key_data': self.key_handler.store(),
        }

    def encrypt(self, plaintext): 
        cipher = self.cipher
        iv = Random.new().read(cipher.block_size)
        padding = ' ' * (-len(plaintext) % cipher.block_size)
        engine = cipher.new(self.key_handler.key, cipher.MODE_CBC, iv)
        return iv + engine.encrypt(plaintext + padding)

    def decrypt(self, ciphertext): 
        cipher = self.cipher
        iv = ciphertext[:cipher.block_size]
        engine = cipher.new(self.key_handler.key, cipher.MODE_CBC, iv)
        return engine.decrypt(ciphertext[cipher.block_size:])
