from tkinter import *
from tkinter.font import Font

class TextBox(Text):
  def __init__(self, parent):
    super().__init__(parent)
    self.padding = parent.padding
    self.font = parent.font
    self.config(wrap=WORD, bg="#000", font=parent.font)
    self.grid(column=1, sticky="nsew", padx=self.padding, pady=self.padding)
    self.bind("<FocusIn>", lambda event, box=self: toggle_bg_colour(box, event))
    self.bind("<FocusOut>", lambda event, box=self: toggle_bg_colour(box, event))

    self.context_menu = Menu(parent, tearoff=0, bg="#111")
    self.context_menu.add_command(label="Copy", command=lambda: self.event_generate("<<Copy>>"))
    self.bind("<Button-3>", lambda event: self.context_menu.tk_popup(event.x_root, event.y_root))

class ThreadBox(TextBox):
  def __init__(self, parent):
    super().__init__(parent)
    self.config(state=DISABLED, fg="#888")
    self.grid(row=0)
    self.tag_configure("user", foreground="#555") 
    self.tag_configure("assistant", foreground="#975") 
    self.tag_configure("system", foreground="#66f") 
    self.tag_configure("prompt", foreground="#66f") 
    self.tag_configure("error", foreground="#f00") 
    self.tag_configure("highlight", background="#ff6", foreground="#000")

  # display current message history in thread_box
  def add_message(self, message, role):
    self.config(state=NORMAL) # enable editing text in thread_box
    if self.index(INSERT) != "1.0":
      self.insert(END, "\n---\n", "system")
    self.insert(END, message, role)
    self.config(state=DISABLED) # disable editing text in thread_box
    self.see(END)

  def clear(self):
    self.config(state=NORMAL)
    self.delete("1.0", "end")
    self.config(state=DISABLED)

class InputBox(TextBox):
  def __init__(self, parent):
    super().__init__(parent)
    self.config(insertbackground="#888", undo=True, height=1, fg="#555", bg="#000")
    self.width = self.winfo_width()
    self.grid(row=1)
    self.context_menu.add_command(label="Cut", command=lambda: self.event_generate("<<Cut>>"))
    self.context_menu.add_command(label="Paste", command=lambda: self.event_generate("<<Paste>>"))
    self.bind("<Shift-Return>", self.input_newline)
    self.bind("<KeyPress>", self.resize)
    self.bind("<KeyRelease>", self.resize)
    self.focus_set()

  # Shift-Return
  def input_newline(self, event=None):
    self.insert(INSERT, "\n")
    return "break"

  # dynamically resize input_box while typing or resizing window
  def resize(self, event=None):
    input_width = self.winfo_width()
    num_lines = 0
    for line in self.get("1.0", "end").splitlines():
      num_lines += 1 + int(self.font.measure(line) / input_width)
    self.config(height=min(num_lines, 20))
    self.see(INSERT)

  def get_message(self):
    message = self.get("1.0", "end").strip()
    self.delete("1.0", "end")
    return message

# clarify caret location
def toggle_bg_colour(box, event=None):
  if event.type == "9": # <FocusIn>
    box.config(background="#080808")
  elif event.type == "10": # <FocusOut>
    box.config(background="#000")