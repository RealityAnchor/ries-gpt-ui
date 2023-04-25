'''
main_window.py
Adam Ries, adamalexanderries{}gmail{}com
2023-04-06
tkinter desktop chat interface for interacting with GPT-3 via OpenAI's API
'''

# built in
from datetime import datetime
import json
import os
import re
import threading
from tkinter import *
from tkinter.simpledialog import askstring
from tkinter.font import Font

# pip install
import tiktoken

# custom
from search_window import SearchWindow
from text_box import ThreadBox, InputBox
import gpt


# main tkinter window
class MainWindow(Tk):
  def __init__(self):
    super().__init__()
    self.init_variables()
    self.update()
    
    # Text widgets
    self.thread_box = ThreadBox(self)
    self.input_box = InputBox(self)

    # Menu
    # Saved - manually-titled message threads
    # History - timestamp-titled message threads
    self.option_add("*Menu*activeBackground", "#333")
    self.option_add("*Menu*activeForeground", "#975")
    self.option_add("*Menu*background", "#000")
    self.option_add("*Menu*foreground", "#975")
    self.menu = Menu(self, background="#333", foreground="#FFF", activebackground="#555", activeforeground="#FFF")
    self.history_menu = Menu(self, background="#333", foreground="#FFF", activebackground="#555", activeforeground="#FFF", tearoff=0)
    self.save_menu = Menu(self, background="#333", foreground="#FFF", activebackground="#555", activeforeground="#FFF", tearoff=0)
    self.menu.add_cascade(label="Saved", menu=self.save_menu)
    self.menu.add_cascade(label="History", menu=self.history_menu)
    self.config(menu=self.menu)

    # set up preprompt menu
    self.pp = None
    self.pp_title = StringVar(self, "Default")
    self.pp_title_list = self.get_pp_titles()
    self.pp_menu = OptionMenu(self, self.pp_title, self.pp_title_list, command=self.set_pp)
    self.pp_menu.grid(row=1, column=2, sticky=S+E+W, padx=(0, self.padding), pady=(0, self.padding))
    self.pp_menu.configure(background="#333", foreground="#FFF", activebackground="#555", activeforeground="#FFF", relief="raised", direction="above")
    self.pp_menu.bind("<Enter>", self.on_pp_hover)
    self.pp_menu.bind("<Leave>", self.on_pp_hover)
    self.populate_pp_menu()
    self.bind_shortcuts()

    # configure layout spacing
    self.grid_columnconfigure(0, weight = 1)
    self.grid_columnconfigure(1, weight = 4)
    self.grid_columnconfigure(2, weight = 1)
    self.grid_rowconfigure(0, weight=1)
    self.grid_rowconfigure(1, weight=0)

    self.update()
    self.new_conversation()
    
  def init_variables(self):
    self.engine = "gpt-3.5-turbo"
    self.title(self.engine)
    self.state("zoomed")
    self.minsize(500, 500)
    self.configure(bg="#040404") # dark grey background
    self.history = []
    self.padding = 8

    # tokenization is done to measure thread length
    # gpt-3.5-turbo can't handle more than 4096 tokens
    # long threads are sliced to allow for at least 1000 response tokens
    self.encoding = tiktoken.encoding_for_model(self.engine)
    self.max_tokens = 3096
    self.history_slice_index = 0
    self.slice_token_index = 0

    # thread title set to current date and time yyyy-mm-dd_hhmmss
    self.timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    self.filename = self.timestamp
    self.font = Font(family="Arial", size=14)
    self.search_window_attributes = {}
    self.search_window = None
    self.protocol("WM_DELETE_WINDOW", self.on_close)

  def bind_shortcuts(self):
    self.bind("<Return>", self.send_message)
    self.bind("<Configure>", self.resize_window) # keep horizontal padding proportional to window width
    self.bind("<Control-e>", self.toggle_box_focus) # toggle focus between input and thread box
    self.bind("<Control-f>", self.toggle_search_window)
    self.bind("<Control-s>", self.rename_thread) # change filename and title
    self.bind("<Control-w>", self.on_close) # close current window
    self.bind("<F5>", self.new_conversation) # clear thread_box, prepare for new file
    self.bind("<F11>", self.toggle_fullscreen)

  #-----------#
  # Messaging #
  #-----------#

  # Return
  def send_message(self, event=None):
    user_prompt = self.input_box.get_message()
    self.history.append({"role": "user", "content": user_prompt})
    self.thread_box.add_message(user_prompt, "user")
    self.save_file()
    # make GPT API call to OpenAI with current message thread
    t = threading.Thread(target=self.invoke_gpt, args=(self.engine, self.truncated_thread()))
    t.start()
    return "break" # no newline character

  # reduce long threads to not send more than max_tokens via API call
  def truncated_thread(self):
    thread = self.history.copy()
    thread_token_counts = [len(self.encoding.encode(entry["content"])) for entry in self.history]
    while sum(thread_token_counts) > self.max_tokens:
      thread_token_counts.pop(0)
    if len(thread_token_counts) < len(self.history):
      thread = thread[-(len(thread_token_counts)+1):]
      # first_message_token_count = len(self.encoding.encode(thread[0]["content"]))
      truncate_index = self.max_tokens - sum(thread_token_counts)
      thread[0]["content"] = self.encoding.decode(self.encoding.encode(thread[0]["content"])[-truncate_index:])
    return thread

  def invoke_gpt(self, engine, history):
    try:
      if self.pp:
        history.insert(-1, {"role": "system", "content": self.pp}) # Preprompt included as last message
      response = gpt.api_call(engine, history) # using ChatCompletion
      if self.pp:
        history.pop(-1) # Preprompt removed (not included in history)
      gpt_response = response["choices"][0]["message"]["content"]
      self.history.append({"role": "assistant", "content": gpt_response})
      self.thread_box.add_message(gpt_response, "assistant")
      self.save_file()
    except Exception as err:
      self.thread_box.config(state=NORMAL)
      self.thread_box.insert(END, f"\n\n{err}", "error")
      self.thread_box.config(state=DISABLED)
      self.thread_box.see(END)

  # Ctrl-E
  def toggle_box_focus(self, event=None):
    if self.focus_get() == self.input_box:
      self.thread_box.focus_set()
    else:
      self.input_box.focus_set()

  #---------------#
  # Search Window #
  #---------------#

  # Ctrl-F
  def toggle_search_window(self, event=None):
    if not self.search_window_attributes: # set default attributes
      self.search_window_attributes["position"] = f"+{int(self.winfo_rootx() + self.winfo_width() / 2)}+{int(self.winfo_rooty() + self.winfo_height() / 2)}" # center window
      self.search_window_attributes["history"] = False # search only in this file
      self.search_window_attributes["backwards"] = True # search forwards
      self.search_window_attributes["query"] = "" # empty search string
    if self.search_window: # do not make new search window if one already exists
      self.search_window.search_entry.focus_set()
    else:
      search_window = SearchWindow(self, self.search_window_attributes)
      self.search_window = search_window

  #--------------------#
  # Title and filename #
  #--------------------#
      
  # Ctrl-S
  def rename_thread(self, event=None):
    old_filename = self.filename
    new_filename = askstring("Rename Conversation", "")
    if new_filename:
      # check for duplicates
      historydir = os.path.join(os.path.dirname(__file__),"history")
      existing_files = [f.rsplit(".", 1)[0] for f in os.listdir(historydir)]
      i = 2 # duplicate_filename_2, _3, _4, ...
      while new_filename in existing_files:
        new_filename = f"{new_filename.rsplit('_', 1)[0]}_{i}"
        i += 1
      # rename file and update menu
      filepathold = os.path.join(os.path.dirname(__file__),"history",old_filename)
      filepathnew = os.path.join(os.path.dirname(__file__),"history",new_filename)
      os.rename(f"{filepathold}.json", f"{filepathnew}.json")
      self.filename = new_filename
      self.save_file()
      self.filename_list = self.get_history_filenames("history", ".json")
      self.populate_history_menu(self.filename_list)

  # F5
  def new_conversation(self, event=None):
    self.history = []
    self.timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    self.filename = self.timestamp
    self.filename_list = self.get_history_filenames("history", ".json")
    self.populate_history_menu(self.filename_list)
    self.title(self.engine)
    self.thread_box.clear()

  def update_title(self, filename):
    filepath = os.path.join(os.path.dirname(__file__),"history",filename)
    file_size = round(os.path.getsize(f"{filepath}.json") / 1024, 1)
    self.title(f"{filename} ({file_size} KB)") # tkinter window title

  def save_file(self):
    filepath = os.path.join(os.path.dirname(__file__),"history",self.filename)
    with open(f"{filepath}.json", "w") as f:
      json.dump(self.history, f)
    self.update_title(self.filename)

  def load_file(self, filename):
    dirname = os.path.dirname(__file__)
    filepath = os.path.join(dirname, 'history', filename)
    with open(f"{filepath}.json", "r") as f:
      self.history = json.load(f)
    self.filename_list = self.get_history_filenames("history", ".json")
    self.filename = filename
    self.thread_box.clear()
    for m in self.history:
      self.thread_box.add_message(m["content"], m["role"])
    self.update_title(filename)

  #----------------#
  # Preprompt menu #
  #----------------#

  def set_pp(self, title="Default"):
    if title == "Default":
      self.pp = None
      self.pp_title.set("Default")
    else:  
      self.pp = self.pp_list[title]
      self.pp_title.set(title)

  def populate_pp_menu(self):
    self.pp_menu["menu"].delete(0, "end")
    self.pp_menu["menu"].add_command(label="Default", font=self.font, command=lambda t="Default": self.set_pp(t))
    for k,v in self.pp_list.items():
      self.pp_menu["menu"].add_command(label=k, font=self.font, command=lambda t=k: self.set_pp(t))

  def get_pp_titles(self):
   with open("preprompts.json") as f:
     pp_data = json.load(f)
     self.pp_list = {p['title']: p['prompt'] for p in pp_data}
     self.pp_title_list = ["Default"] + [k for k,v in self.pp_list.items()]

  def on_pp_hover(self, event):
    if event.type == "7":
      if self.pp:
        hover_text = self.pp
        hover_colour = "#66f"
      else:
        hover_text = "Default: no preprompt."
        hover_colour = "#555"
      text_width = self.font.measure(hover_text)
      window_width = self.winfo_width()
      max_width = int(window_width / 2.5)
      x = int((window_width - min(max_width, text_width + self.padding) - self.pp_menu.winfo_width()) / 2)
      y = int((self.winfo_height() - self.font.metrics("linespace") * text_width / max_width) / 2)
      self.pp_hover_label = Toplevel(self.pp_menu)
      self.pp_hover_label.wm_overrideredirect(True)
      self.pp_hover_label.wm_geometry(f"+{x}+{y}")
      label = Label(self.pp_hover_label, text=hover_text, wraplength=max_width, bg="#000", fg=hover_colour, font=self.font, relief="raised", justify=LEFT)
      label.pack()
    elif event.type == "8":
      if self.pp_hover_label:
        self.pp_hover_label.destroy()

  #--------------#
  # History menu #
  #--------------#

  def get_history_filenames(self, directory, ext):
    dirname = os.path.dirname(__file__)
    filenames = os.listdir(f"{os.path.join(dirname,directory)}/")
    # include only filenames with correct extension
    out_filenames = sorted([f.rsplit(".", 1)[0] for f in filenames if f.endswith(ext)], reverse=True)
    return out_filenames
  
  def populate_history_menu(self, filenames):
    self.menu.delete("Saved")
    self.menu.delete("History")
    self.save_menu.delete(0, END)
    dirname = os.path.dirname(__file__)
    for filename in filenames:
      historyfolder = "history"
      filepath = f"{os.path.join(dirname, historyfolder, filename)}.json"
      file_size = round(os.path.getsize(filepath) / 1024, 1)
      if re.match(r"\d{4}-\d{2}-\d{2}_\d{6}", filename): # yyyy-mm-dd_hhmmss default filename
        cur_menu = self.history_menu
      else: # custom filename
        cur_menu = self.save_menu
      cur_menu.add_command(label=f"{filename} ({file_size} KB)", command=lambda name=filename: self.load_file(name)) # load file on click
    self.menu.add_cascade(label="Saved", menu=self.save_menu)
    self.menu.add_cascade(label="History", menu=self.history_menu)

  #--------#
  # Window #
  #--------#

  # F11
  def toggle_fullscreen(self, event=None):
    self.attributes("-fullscreen", not self.attributes("-fullscreen"))
    
  # Configure
  # update formatting dynamically whenever window changes size or position
  def resize_window(self, event=None):
    self.input_box.resize()

  # cleanup tkinter windows
  def on_close(self, event=None):
    if self.search_window:
      self.search_window.destroy()
    self.destroy()

if __name__ == "__main__":
  root = MainWindow()
  root.iconbitmap(os.path.join(os.path.dirname(__file__),"icon.ico"))
  root.mainloop()
