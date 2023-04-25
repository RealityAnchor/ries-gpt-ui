from tkinter import *
from tkinter import ttk
from tkinter.simpledialog import askstring
import os
import json

# Ctrl-f function in MainWindow opens a SearchWindow
# Toplevel specifies that this is a subclass of another tkinter window
class SearchWindow(Toplevel):
  def __init__(self, parent, attributes=None):
    super().__init__(parent)
    self.title("SearchWindow")
    self.parent = parent
    self.resizable(False, False)
    self.cur_file_index = 0
    self.cur_char_index = ""
    
    self.attr = attributes
    self.search_history = BooleanVar()
    self.search_backwards = BooleanVar()
    self.search_entry = Entry(self, width=30)
    
    # 
    if self.attr:
      self.geometry(self.attr["position"])
      self.search_history.set(self.attr["history"])
      self.search_backwards.set(self.attr["backwards"])
      self.search_entry.insert(END, self.attr['query'])
    else: # redundant with default attribute settings in MainWindow
      self.geometry("+100+100")
      self.search_history.set(False)
      self.search_backwards.set(True)

    self.search_entry.bind("<Return>", self.increment_search)
    self.bind("<Control-g>", lambda event: self.toggle_search_history())
    self.bind("<Control-d>", lambda event: self.toggle_search_backwards())
    # different ways to close
    self.bind("<Control-f>", self.on_close) # toggle window
    self.bind("<Escape>", self.on_close)
    self.protocol("WM_DELETE_WINDOW", self.on_close) 

    # buttons
    search_button = ttk.Button(self, text="Search", command=self.increment_search)
    self.search_backwards_toggle = ttk.Checkbutton(self, text="Backwards search [Ctrl-D]", variable=self.search_backwards)
    self.search_history_toggle = ttk.Checkbutton(self, text="File search [Ctrl-G]", variable=self.search_history)
    
    # formatting
    self.search_entry.grid(row=0, column=0, padx=(5,0), pady=5)
    search_button.grid(row=0, column=1, padx=(5,5), pady=5)
    self.search_backwards_toggle.grid(row=1,column=0, padx=5, sticky="w")
    self.search_history_toggle.grid(row=2,column=0, padx=5, sticky="w")
    self.search_entry.focus_set()

  # Ctrl-G
  def toggle_search_history(self):
    toggled_history = not self.search_history.get()
    self.search_history.set(toggled_history)
    self.parent.search_window_attributes["history"] = toggled_history

  # Ctrl-D
  def toggle_search_backwards(self):
    toggled_backwards = not self.search_backwards.get()
    self.search_backwards.set(toggled_backwards)
    self.parent.search_window_attributes["backwards"] = toggled_backwards

  # find the next or the previous term, in all files or current file
  def increment_search(self, event=None):
    backwards = self.search_backwards.get()
    query = self.search_entry.get().lower()
    self.parent.search_window_attributes["query"] = query
    if not query:
      return
    
    if self.search_history.get(): # search all files in history
      matching_filenames = self.get_json_filenames("history", query)
      self.parent.populate_history_menu(matching_filenames)
      file_count = len(matching_filenames)
      if file_count > 0:
        if backwards:
          if self.cur_file_index == 0:
            self.cur_file_index = file_count - 1
          else:
            self.cur_file_index -= 1
        else:
          if self.cur_file_index < file_count - 1:
            self.cur_file_index += 1
          else:
            self.cur_file_index = 0
        self.parent.load_file(matching_filenames[self.cur_file_index])
        # refactor so that i can self.increment_search(search_history=False)
        self.toggle_search_history()
        self.increment_search()
        self.toggle_search_history()

    else: # search current thread
      if self.cur_char_index == "": # when search begins
        self.cur_char_index = END if backwards else "1.0" # search back to front or front to back
      if not backwards:
        self.cur_char_index = f"{self.cur_char_index}+1c" # increment to prevent returning same string repeatedly
      self.cur_char_index = self.find_next_string(query, self.cur_char_index, backwards) # highlight match in MainWindow

  def find_next_string(self, query_string, starting_index, backwards=False):
    first_char_index = None
    last_char_index = None
    first_char_index = self.parent.thread_box.search(query_string, starting_index, nocase=True, backwards=backwards)
    if first_char_index: # add highlighting on matches
      self.parent.thread_box.tag_remove("highlight", "1.0", END)
      last_char_index = f"{first_char_index}+{len(query_string)}c"
      self.parent.thread_box.tag_add("highlight", first_char_index, last_char_index)
      self.parent.thread_box.see(first_char_index)
    return first_char_index

  # return all json files in specified folder which contain the search terms
  def get_json_filenames(self, folder, query):
    results = []
    for filename in os.listdir(folder):
      title, ext = os.path.splitext(filename)
      if ext == ".json":
        with open(os.path.join(folder, filename), "r") as file:
          data = json.load(file)
          for entry in data:
            if query.lower() in entry["content"].lower():
              results.append(title)
              break # after finding a match, stop searching in current file
    return results

  # parent MainWindow cleanup:
  # remove highlights
  # store current window position and search string
  def on_close(self, event=None):
    self.parent.thread_box.tag_remove("highlight", "1.0", END)
    self.parent.search_window = None
    self.parent.search_window_attributes["position"] = self.geometry()
    self.parent.search_window_attributes["query"] = self.search_entry.get().lower()
    super().destroy()
