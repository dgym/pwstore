import sys
import os
import readline
from getpass import getpass

from store import Store


class CLI(object):
    def __init__(self, filename):
        self.filename = filename
        self.store = Store()

        if os.path.exists(filename):
            self.passphrase = self.get_passphrase()
            self.store.load(self.passphrase, filename)
        else:
            self.passphrase = self.get_passphrase(confirm=True)
            self.store.create(self.passphrase)

        self.commands = {
            'ls' : (self.cmd_list, 'l'),
            'cat' : (self.cmd_cat, 'c:'),
            'set' : (self.cmd_set, 's:'),
            'rm' : (self.cmd_remove, 'r:'),
            'save' : (self.cmd_save, ' '),
            'change_passphrase': (self.cmd_change_passphrase, ' '),
        }


    def cmd_list(self):
        print '\n'.join(sorted(self.store.entries.iterkeys()))

    def cmd_cat(self, label):
        entry = self.store.entries.get(label)
        if entry is not None:
            print entry
        else:
            print 'ERROR: label not found'

    def cmd_set(self, label):
        value = ''
        while True:
            line = sys.stdin.readline()
            if line[0] == '\r' or line[0] == '\n':
                break
            value += line
        self.store.entries[label] = value.strip()
        self.store.modified = True

    def cmd_remove(self, label):
        try:
            del self.store.entries[label]
            self.store.modified = True
        except KeyError:
            print 'ERROR: label not found'

    def cmd_save(self):
        self.store.save(self.filename)

    def cmd_change_passphrase(self):
        current = self.get_passphrase(prompt="Current passphrase: ")
        if current != self.passphrase:
            print 'Incorrect, passphrase not changed.'
            return
        new_passphrase = self.get_passphrase(confirm=True, allow_blank=True)
        if not new_passphrase:
            print 'Passphrase not changed.'
        else:
            self.passphrase = new_passphrase
            self.store.change_passphrase(new_passphrase)

    def completer(self, text, state):
        parts = readline.get_line_buffer().split(' ')
        idx = len(parts)

        if idx == 1:
            matches = 0
            for command, attrs in self.commands.items():
                if command.startswith(text):
                    matches += 1
                    if matches > state:
                        if attrs[-1][-1] == ':':
                            command += ' '
                        return command
        elif idx == 2:
            matches = 0
            for label in self.store.entries.iterkeys():
                if label.startswith(text):
                    matches += 1
                    if matches > state:
                        return label

    def get_passphrase(self, prompt=None, confirm=False, allow_blank=False):
        while True:
            passphrase = getpass(prompt or "Passphrase: ")
            if not passphrase:
                if allow_blank:
                    return
                continue

            if confirm:
                again = getpass("Confirm passphrase: ")
                if passphrase != again:
                    print 'Passphrases did not match, please try again.'
                    continue

            break
        return passphrase

    def run(self):
        readline.set_completer(self.completer)

        while True:
            try:
                command = raw_input('*> ' if self.store.modified else '> ')
            except EOFError:
                print
                break
            parts = command.split(' ')
            if len(parts):
                proc, _ = self.commands.get(parts[0], (None, None))
                if proc:
                    proc(*parts[1:])


def main():
    # Set up readline to tab complete.
    readline.parse_and_bind('tab: complete')
    # Remove '-' from the word delimiters.
    delims = readline.get_completer_delims()
    readline.set_completer_delims(delims.replace('-', ''))

    cli = CLI(sys.argv[1])
    cli.run()


if __name__ == '__main__':
    main()
