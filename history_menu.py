from tkinter import *
import json
import os

class HistoryMenu(OptionMenu):
  def __init__(self, parent, title):
    super().__init__(parent, title, "Default")
    self.option_add("*Menu*activeBackground", "#333")
    self.option_add("*Menu*activeForeground", "#975")
    self.option_add("*Menu*background", "#000")
    self.option_add("*Menu*foreground", "#975")
    self.parent = parent
    self.font = parent.font
    self.padding = parent.padding
    self.directory = parent.directory
    self.history_title = StringVar(self, "History")
    self.history_filename_list = self.get_history_titles()
    self.grid(row=1, column=0, sticky=S+E+W, padx=(self.padding, 0), pady=(0, self.padding))
    self.configure(background="#333", foreground="#FFF",
        activebackground="#555", activeforeground="#FFF",
        relief="raised", direction="above")
    self.option_add("*Menu*activeBackground", "#333")
    self.option_add("*Menu*activeForeground", "#975")
    self.option_add("*Menu*background", "#000")
    self.option_add("*Menu*foreground", "#975")
    self.populate()

  def populate(self):
    self["menu"].delete(0, "end")
    for filename in self.history_filename_list:
      filepath = os.path.join(self.directory, "history", filename)
      file_size = round(os.path.getsize(f"{filepath}.json") / 1024, 1)
      self["menu"].add_command(label=f"{filename} ({file_size} KB)",
          font=self.font, command=lambda f=filename: self.parent.load_file(f))

  def get_history_titles(self):
    filenames = os.listdir(os.path.join(self.parent.directory,"history"))
    filenames = sorted([f.rsplit(".", 1)[0] for f in filenames if f.endswith(".json")], reverse=True)
    return filenames