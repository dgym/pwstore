import re
import json
from base64 import b64encode, b64decode
from getpass import getpass
import readline
from hashlib import sha512
from collections import OrderedDict

from ciphers import CIPHERS
from key_handler import KEY_HANDLERS
from stage import Stage


class Store(object):
    def __init__(self):
        self.stages = []
        self.key = None
        self.entries = {}

    def load(self, filename):
        with open(filename, 'r') as stream:
            contents = stream.read()
        contents = json.loads(contents)

        self.stages = []
        for idx, parameters in enumerate(contents['stages'], 1):
            cipher_name = parameters['cipher']
            cipher = CIPHERS[cipher_name]
            key_handler = KEY_HANDLERS[parameters['key_handler']]()
            while True:
                key_handler.passphrase = self.get_password(idx)
                if not key_handler.load(
                        cipher.key_size[-1],
                        parameters['key_data']):
                    print 'Bad password'
                else:
                    break
            self.stages.append(Stage(cipher_name, cipher, key_handler))

        ciphertext = b64decode(contents['ciphertext'])
        for stage in reversed(self.stages):
            ciphertext = stage.decrypt(ciphertext)

        match = re.match(r'check:(\d+):([^:]+):(.*)', ciphertext)
        if not match:
            raise ValueError('Bad password used, decrypt failed')
        length = int(match.group(1))
        digest = match.group(2)
        plaintext = match.group(3)[:length]
        if not digest == sha512(plaintext).hexdigest():
            raise ValueError('Bad password used, decrypt failed')
        self.entries = json.loads(plaintext)

    def create(self):
        self.stages = []
        while True:
            stage = len(self.stages) + 1

            cipher_name = self.get_choice(
                'Select stage %i encryption cipher []: ' % stage,
                CIPHERS.keys(),
            )
            cipher = CIPHERS[cipher_name]
            
            key_handler = self.get_choice(
                'Select stage %i key handler []: ' % stage,
                KEY_HANDLERS,
            )()
            options = {}
            for option in key_handler.options:
                while True:
                    value = raw_input(
                        '%s (%s): ' % (option.name, option.help_text),
                    )
                    if option.check and not re.match(option.check, value):
                        continue
                    options[option.name] = option.converter(value)
                    break
            key_handler.passphrase = self.get_password(stage, confirm=True)

            key_handler.make_key(cipher.key_size[-1], options)
            self.stages.append(Stage(cipher_name, cipher, key_handler))

            if self.get_choice('Add another stage []: ', 'yn') == 'n':
                break

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

    def get_password(self, stage_idx, confirm=False):
        while True:
            password = getpass("Passphrase for stage %i: " % stage_idx)
            if not password:
                continue

            if confirm:
                again = getpass("Repeat passphrase for stage %i: " % stage_idx)
                if password != again:
                    print 'Passphrases did not match, please try again.'
                    continue

            break
        return password

    def get_choice(self, prompt, choices):
        keys = choices.keys() if isinstance(choices, dict) else choices
        prompt = prompt.replace('[]', '[%s]' % ','.join(keys))

        def completer(text, state):
            matches = 0
            for choice in choices:
                if choice.startswith(text):
                    matches += 1
                    if matches > state:
                        return choice

        readline.set_completer(completer)

        while True:
            choice = raw_input(prompt)
            if choice in keys:
                return choices[choice] if isinstance(choices, dict) else choice
