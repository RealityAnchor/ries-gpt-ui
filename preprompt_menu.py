from tkinter import *
import json

class PrepromptMenu(OptionMenu):
  def __init__(self, parent, title):
    super().__init__(parent, title, "Default")
    self.pp = None
    self.font = parent.font
    self.padding = parent.padding
    self.parent = parent
    self.pp_title = StringVar(self, "Default")
    self.pp_title_list = self.get_pp_titles()
    self.grid(row=1, column=2, sticky=S+E+W, padx=(0, self.padding), pady=(0, self.padding))
    self.configure(background="#333", foreground="#FFF",
        activebackground="#555", activeforeground="#FFF",
        relief="raised", direction="above")
    self.bind("<Enter>", self.on_pp_hover)
    self.bind("<Leave>", self.on_pp_hover)
    self.populate_pp_menu()

  def set_pp(self, title="Default"):
    if title == "Default":
      self.pp = None
    else:  
      self.pp = self.pp_list[title]
    self.parent.pp_title.set(title)

  def populate_pp_menu(self):
    self["menu"].delete(0, "end")
    self["menu"].add_command(label="Default", font=self.font, command=lambda t="Default": self.set_pp(t))
    for k,v in self.pp_list.items():
      self["menu"].add_command(label=k, font=self.font, command=lambda t=k: self.set_pp(t))

  def get_pp_titles(self):
   with open("preprompts.json") as f:
     pp_data = json.load(f)
     self.pp_list = {p['title']: p['prompt'] for p in pp_data}
     return ["Default"] + [k for k,v in self.pp_list.items()]

  def on_pp_hover(self, event):
    if event.type == "7":
      if self.pp:
        hover_text = self.pp
        hover_colour = "#66f"
      else:
        hover_text = "Default: no preprompt."
        hover_colour = "#555"
      text_width = self.font.measure(hover_text)
      screen_width = self.parent.winfo_screenwidth()
      screen_height = self.parent.winfo_screenheight()
      max_width = int(screen_width / 2.5)
      text_width = min(self.font.measure(hover_text), max_width)
      text_height = int(self.font.metrics("linespace") * text_width / max_width)
      x = int((screen_width - text_width) / 2)
      y = int((screen_height - text_height) / 2)
      self.pp_hover_label = Toplevel(self)
      self.pp_hover_label.wm_overrideredirect(True)
      self.pp_hover_label.wm_geometry(f"+{x}+{y}")
      label = Label(self.pp_hover_label, text=hover_text, wraplength=max_width, bg="#000", fg=hover_colour, font=self.font, relief="raised", justify=LEFT)
      label.pack()
    elif event.type == "8":
      if self.pp_hover_label:
        self.pp_hover_label.destroy()