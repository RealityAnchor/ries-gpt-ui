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
from preprompt_menu import PrepromptMenu
from preprompt_editor import PrepromptEditor
from history_menu import HistoryMenu
import gpt


# main tkinter window
class MainWindow(Tk):
  def __init__(self):
    super().__init__()
    self.init_variables()
    self.update()
    
    # input and output widgets
    self.input_box = InputBox(self)
    self.thread_box = ThreadBox(self)

    # thread history menu
    self.history_title = StringVar(self, "History")
    self.history_menu = HistoryMenu(self, self.history_title)

    # preprompt menu
    self.pp_title = StringVar(self, "Default")
    self.pp_menu = PrepromptMenu(self, self.pp_title)

    # format grid
    self.grid_columnconfigure(0, weight = 1)
    self.grid_columnconfigure(1, weight = 4)
    self.grid_columnconfigure(2, weight = 1)
    self.grid_rowconfigure(0, weight=1)
    self.grid_rowconfigure(1, weight=0)

    self.update()
    self.bind_shortcuts()
    self.new_conversation()
    
  def init_variables(self):
    self.directory = os.path.dirname(__file__)
    self.engine = "gpt-3.5-turbo"
    self.title(self.engine)
    self.state("zoomed")
    self.minsize(500, 500)
    self.configure(bg="#040404") # dark grey background
    self.history = []
    self.padding = 8
    # tokenization is done to measure thread length
    # gpt-3.5-turbo can't handle more than 4096 tokens
    # long threads are truncated to allow for at least 1000 response tokens
    self.encoding = tiktoken.encoding_for_model(self.engine)
    self.max_tokens = 3096
    self.history_slice_index = 0
    self.slice_token_index = 0
    # thread title set to current date and time yyyy-mm-dd_hhmmss
    self.filename = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    self.font = Font(family="Arial", size=14)
    self.search_window_attributes = {}
    self.search_window = None
    self.pp_editor = None
    self.protocol("WM_DELETE_WINDOW", self.on_close)

  def bind_shortcuts(self):
    self.bind("<Return>", self.send_message)
    self.bind("<Configure>", self.resize_window) # keep horizontal padding proportional to window width
    self.bind("<Control-e>", self.toggle_box_focus) # toggle focus between input and thread box
    self.bind("<Control-f>", self.toggle_search_window)
    self.bind("<Control-w>", self.on_close) # close current window
    self.bind("<Control-p>", self.toggle_pp_editor)
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
      if self.pp_menu.pp:
        history.insert(-1, {"role": "system", "content": self.pp_menu.pp}) # Preprompt included as last message
      response = gpt.api_call(engine, history) # using ChatCompletion
      if self.pp_menu.pp:
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

  def save_file(self):
    filepath = os.path.join(self.directory, "history", self.filename)
    with open(f"{filepath}.json", "w") as f:
      json.dump(self.history, f)

  #-----------#
  # Shortcuts #
  #-----------#

  # Ctrl-E
  def toggle_box_focus(self, event=None):
    if self.focus_get() == self.input_box:
      self.thread_box.focus_set()
    else:
      self.input_box.focus_set()

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

  # Ctrl-P
  def toggle_pp_editor(self, event=None):
    if self.pp_editor:
      self.pp_editor.destroy()
      self.pp_editor = None
    else:
      self.pp_editor = PrepromptEditor(self)

  # F5
  def new_conversation(self, event=None):
    self.history = []
    self.title(self.engine)
    self.thread_box.clear()

  # F11
  def toggle_fullscreen(self, event=None):
    self.attributes("-fullscreen", not self.attributes("-fullscreen"))

  #--------#
  # Window #
  #--------#

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
  root.iconbitmap(os.path.join(os.path.dirname(__file__), "icon.ico"))
  root.mainloop()
