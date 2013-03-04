import sys
import os
import Tkinter as tkinter

from store import Store


class Dialog(tkinter.Toplevel):
    def __init__(self, parent, title=None, label=None):
        tkinter.Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent
        self.label = label
        self.buttons = {}
        self.value = None
        self.entry = None

        body = tkinter.Frame(self)
        self.initial_focus = self.build(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()
        self.success = False

    def run(self):
        self.success = False
        self.wait_window(self)
        return self.success

    def build(self, master):
        label = tkinter.Label(master, text=self.label)
        label.grid(row=0, sticky=tkinter.W)
        self.entry = tkinter.Entry(master)
        self.entry.grid(row=0, column=1)
        return self.entry

    def buttonbox(self):
        box = tkinter.Frame(self)

        w = tkinter.Button(
            box,
            text="OK",
            width=10,
            command=self.on_ok,
            default=tkinter.ACTIVE,
        )
        w.pack(side=tkinter.LEFT, padx=5, pady=5)
        self.buttons['ok'] = w

        w = tkinter.Button(
            box,
            text="Cancel",
            width=10,
            command=self.on_cancel,
        )
        w.pack(side=tkinter.LEFT, padx=5, pady=5)
        self.buttons['cancel'] = w

        self.bind("<Return>", self.on_ok)
        self.bind("<Escape>", self.on_cancel)

        box.pack()

    def on_ok(self, _event=None):
        if not self.validate():
            self.initial_focus.focus_set()
            return

        self.withdraw()
        self.update_idletasks()

        self.success = True
        self.on_cancel()

    def on_cancel(self, _event=None):
        self.parent.focus_set()
        self.destroy()

    def validate(self):
        self.value = self.entry.get()
        return True


class PassphraseDialog(Dialog):
    passphrase = None
    confirm = None

    def __init__(self, parent, title=None, confirm=False):
        self.confirm = confirm
        Dialog.__init__(self, parent, title)
        self.on_key()

    def build(self, master):
        label = tkinter.Label(master, text="Passphrase:")
        label.grid(row=0, sticky=tkinter.W)
        self.entry = tkinter.Entry(master, show='*')
        self.entry.grid(row=0, column=1)

        if self.confirm:
            label = tkinter.Label(master, text="Confirm passphrase:")
            label.grid(row=1, sticky=tkinter.W)
            self.confirm = tkinter.Entry(master, show='*')
            self.confirm.grid(row=1, column=1)

            self.entry.bind("<KeyRelease>", self.on_key)
            self.confirm.bind("<KeyRelease>", self.on_key)

        return self.entry

    def validate(self):
        if self.confirm and self.entry.get() != self.confirm.get():
            return False
        self.passphrase = self.entry.get()
        return True

    def on_key(self, *_args):
        if not self.confirm:
            return
        enabled = self.entry.get() and self.entry.get() == self.confirm.get()
        button = self.buttons['ok']
        button.config(state=(tkinter.NORMAL if enabled else tkinter.DISABLED))



class GUI(object):
    def __init__(self, filename):
        self.filename = filename
        self.store = Store()
        self.root = tkinter.Tk()
        self.passphrase = None
        self.selected = None
        self.value_changing = False

        left_frame = tkinter.Frame(self.root)
        left_frame.pack(side=tkinter.LEFT, fill=tkinter.Y)
        left_frame.rowconfigure(0, weight=1)

        scroll = tkinter.Scrollbar(left_frame)
        self.keys = tkinter.Listbox(left_frame, exportselection=0)

        scroll.grid(row=0, column=1, sticky=tkinter.N+tkinter.S)
        self.keys.grid(row=0, column=0, sticky=tkinter.N+tkinter.S)

        scroll.config(command=self.keys.yview)
        self.keys.config(yscrollcommand=scroll.set)

        self.keys.bind("<ButtonRelease>", self.on_key_selected)
        self.keys.bind("<KeyRelease>", self.on_key_selected)

        add = tkinter.Button(
            left_frame,
            text="Add",
            command=self.on_add_entry,
        )
        add.grid(row=1, columnspan=2, sticky=tkinter.E+tkinter.W)

        self.value_box = tkinter.Text(self.root)
        self.value_box.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
        self.value_box.bind('<<Modified>>', self.on_value_changed)

        self.root.bind('<Control-s>', self.on_save)

    def run(self):
        if os.path.exists(self.filename):
            dialog = PassphraseDialog(self.root, title='Passphrase')
            if not dialog.run():
                return
            self.passphrase = dialog.passphrase
            self.store.load(self.passphrase, self.filename)
            self.show_keys()
        else:
            dialog = PassphraseDialog(self.root, title='Passphrase', confirm=True)
            if not dialog.run():
                return
            self.passphrase = dialog.passphrase
            self.store.create(self.passphrase)

        self.update_modified()
        self.root.mainloop()

    def on_key_selected(self, *_args):
        selected = self.keys.curselection()
        if not selected:
            self.selected = None
            return
        idx = int(selected[0])
        self.selected = self.keys.get(idx)
        value = self.store.entries[self.selected]
        self.value_changing = True
        self.value_box.delete(1.0, tkinter.END)
        self.value_box.insert(1.0, value)
        self.value_changing = False

    def on_add_entry(self, *_args):
        dialog = Dialog(self.root, title='Add', label='name')
        if not dialog.run():
            return
        key = dialog.value
        self.store.entries[key] = ''
        self.store.modified = True
        self.update_modified()
        keys = self.show_keys()
        self.keys.select_clear(0, tkinter.END)
        self.keys.select_set(keys.index(key))
        self.on_key_selected()

    def on_value_changed(self, *_args):
        # guard against getting called during key selection changes
        # and also when the modified flag is reset to False.
        if self.value_changing:
            self.root.call(self.value_box, 'edit', 'modified', 0)
            return
        self.value_changing = True
        self.root.call(self.value_box, 'edit', 'modified', 0)
        self.value_changing = False

        if self.selected:
            value = self.value_box.get(1.0, tkinter.END)[:-1]
            if self.store.entries[self.selected] != value:
                self.store.entries[self.selected] = value
                self.store.modified = True
                self.update_modified()

    def on_save(self, *_args):
        self.store.save(self.filename)
        self.update_modified()

    def show_keys(self):
        self.keys.delete(0, tkinter.END)
        keys = self.store.entries.keys()
        keys.sort()
        for key in keys:
            self.keys.insert(tkinter.END, key)
        return keys

    def update_modified(self):
        title = 'Password Store - %s' % self.filename
        if self.store.modified:
            title += ' (*)'
        self.root.title(title)


if __name__ == '__main__':
    GUI(sys.argv[1]).run()
