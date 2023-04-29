from tkinter import Toplevel, StringVar, Entry, END, Button, ttk
import json

class PrepromptEditor(Toplevel):
  def __init__(self, parent):
    super().__init__(parent)
    self.title("PrepromptEditor")
    self.parent = parent
    self.resizable(False, False)
    self.font = parent.font
    self.padding = parent.padding
    self.pp_title = StringVar(self, "Default")

    # Load preprompts from json file
    with open("preprompts.json", "r") as f:
      self.preprompts = json.load(f)

    # Display existing preprompts
    self.tree = ttk.Treeview(self, columns=("Title", "Prompt"), show="headings")
    self.tree.heading("Title", text="Title")
    self.tree.heading("Prompt", text="Prompt")
    self.tree.column("Title", width=200)
    self.tree.column("Prompt", width=400)
    for preprompt in self.preprompts:
      self.tree.insert("", "end", values=(preprompt["title"], preprompt["prompt"]))
    self.tree.pack(padx=self.padding, pady=self.padding)

    # Entry fields to add new preprompt
    self.title_entry = Entry(self, width=30)
    self.title_entry.insert(END, "New Preprompt Title")
    self.title_entry.pack(padx=self.padding, pady=self.padding)
    self.prompt_entry = Entry(self, width=50)
    self.prompt_entry.insert(END, "New Preprompt Prompt")
    self.prompt_entry.pack(padx=self.padding, pady=self.padding)

    # Buttons to add and delete preprompt
    add_button = ttk.Button(self, text="Add Preprompt", command=self.add_preprompt)
    add_button.pack(side="left", padx=self.padding, pady=self.padding)
    delete_button = ttk.Button(self, text="Delete Preprompt", command=self.delete_preprompt)
    delete_button.pack(side="right", padx=self.padding, pady=self.padding)

  # Add new preprompt and refresh display
  def add_preprompt(self):
    new_preprompt = {"title": self.title_entry.get(), "prompt": self.prompt_entry.get()}
    self.preprompts.append(new_preprompt)
    with open("preprompts.json", "w") as f:
        json.dump(self.preprompts, f, indent=2)
    self.tree.insert("", "end", values=(new_preprompt["title"], new_preprompt["prompt"]))
    self.title_entry.delete(0, END)
    self.prompt_entry.delete(0, END)

  # Delete selected preprompt and refresh display
  def delete_preprompt(self):
    selected_iid = self.tree.selection()
    if selected_iid:
      for item in selected_iid:
        self.tree.delete(item)
        self.preprompts.pop(item, None)
      with open("preprompts.json", "w") as f:
        json.dump(self.preprompts, f, indent=2)