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
import gpt

# main tkinter window
class MainWindow(Tk):
    def __init__(self):
        super().__init__()
        self.engine = "gpt-3.5-turbo"
        self.title(self.engine)
        self.state("zoomed")
        self.configure(bg="#080808") # dark grey background
        self.prompt_list = self.get_preprompts("preprompts.json")
        self.prompt = self.prompt_list["default"]["prompt"]
        self.history = []

        # tokenization is done to measure thread length
        # gpt-3.5-turbo can't handle more than 4096 tokens
        # long threads are sliced to allow for at least 1000 response tokens
        self.encoding = tiktoken.encoding_for_model(self.engine)
        self.max_tokens = 3096
        self.slice_index = 0

        # default thread title set to current date and time yyyy-mm-dd_hhmmss
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.filename = self.timestamp

        self.font = Font(family="Arial", size=14)
        self.search_window_attributes = {}
        self.search_window = None
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # thread_box is a Text object displaying current conversation history
        self.update()
        self.x_border = round(self.winfo_width() / 6) # left and right borders each take up 1/6 of total window width
        self.y_border = round(self.winfo_height() / 100)
        self.thread_box = Text(self, wrap=WORD, fg="#555", bg="#000", font=self.font, state=DISABLED)
        self.thread_box.bind("<FocusIn>", lambda event, box=self.thread_box: self.toggle_bg_colour(box, event))
        self.thread_box.bind("<FocusOut>", lambda event, box=self.thread_box: self.toggle_bg_colour(box, event))
        self.thread_box.grid(row=0, column=0, sticky=N+S+E+W, padx=self.x_border, pady=self.y_border)
        self.thread_box.tag_configure("user", foreground="#555") # user input grey
        self.thread_box.tag_configure("assistant", foreground="#975") # AI output gold
        self.thread_box.tag_configure("system", foreground="#66f") # not saved in history
        self.thread_box.tag_configure("prompt", foreground="#66f") # not saved in history
        self.thread_box.tag_configure("error", foreground="#f00") # not saved in history
        self.thread_box.tag_configure("highlight", background="#ff6", foreground="#000") # search function highlight for matches
        
        # input_box is a Text object where user can type or paste text
        self.input_box = Text(self, wrap=WORD, height=1, fg="#888", bg="#000", font=self.font, insertbackground="#888", undo=True)
        self.input_box.bind("<FocusIn>", lambda event, box=self.input_box: self.toggle_bg_colour(box, event))
        self.input_box.bind("<FocusOut>", lambda event, box=self.input_box: self.toggle_bg_colour(box, event))
        self.input_box.grid(row=1, column=0, sticky=N+S+E+W, padx=self.x_border, pady=(0,self.y_border))
        self.input_width = self.input_box.winfo_width()
        self.input_box.focus_set()
        
        # input_box initially takes up only one row
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # shortcut bindings
        self.input_box.bind("<Return>", self.send_message)
        self.input_box.bind("<Shift-Return>", self.input_newline)
        self.input_box.bind("<KeyPress>", self.resize_input)
        self.input_box.bind("<KeyRelease>", self.resize_input)
        self.bind("<Configure>", self.resize_window) # keep horizontal border proportional to window width
        self.bind("<Control-e>", self.toggle_box_focus) # toggle focus between input and thread box
        self.bind("<Control-f>", self.toggle_search_window)
        self.bind("<Control-s>", self.rename_thread) # change filename and title
        self.bind("<Control-w>", self.on_close) # close current window
        self.bind("<F5>", self.new_conversation) # clear thread_box, prepare for new file
        self.bind("<F11>", self.toggle_fullscreen)

        # Menu
        # Preprompts - system message sent with all threads
        # Saved - manually-titled message threads
        # History - timestamp-titled message threads
        self.option_add("*Menu*activeBackground", "#333")
        self.option_add("*Menu*activeForeground", "#975")
        self.option_add("*Menu*background", "#000")
        self.option_add("*Menu*foreground", "#975")
        self.menu = Menu(self, background="#333", foreground="#FFF", activebackground="#555", activeforeground="#FFF")
        self.prompt_menu = Menu(self, background="#333", foreground="#FFF", activebackground="#555", activeforeground="#FFF", tearoff=0)
        self.history_menu = Menu(self, background="#333", foreground="#FFF", activebackground="#555", activeforeground="#FFF", tearoff=0)
        self.save_menu = Menu(self, background="#333", foreground="#FFF", activebackground="#555", activeforeground="#FFF", tearoff=0)  
        self.menu.add_cascade(label="Preprompts", menu=self.prompt_menu)
        self.menu.add_cascade(label="Saved", menu=self.save_menu)
        self.menu.add_cascade(label="History", menu=self.history_menu)
        self.config(menu=self.menu)
        
        self.update()
        self.new_conversation()

    #-----------#
    # Messaging #
    #-----------#

    # Return
    def send_message(self, event=None):
        in_content = f"{self.input_box.get('1.0', 'end').strip()}" # store input
        self.input_box.delete("1.0", END) # clear input
        self.history.append({"role": "user", "content": in_content}) # add input to current thread history
        self.save_file()
        self.update_thread_box()
        # make GPT API call to OpenAI with current message thread
        # multithreading so that program doesn't freeze while waiting for response
        t = threading.Thread(target=self.invoke_gpt, args=(self.engine, self.history[self.slice_index:]))
        t.start()
        return "break" # no newline character

    def invoke_gpt(self, engine, history):
        try:
            history.insert(-1, {"role": "system", "content": self.prompt}) # preprompt included as last message
            response = gpt.api_call(engine, history) # using ChatCompletion
            history.pop(-1) # preprompt removed (not included in history)
            out_content = response["choices"][0]["message"]["content"]
            self.history.append({"role": "assistant", "content": out_content})
            self.save_file()
            self.update_thread_box()
        except Exception as err:
            self.thread_box.config(state=NORMAL)
            self.thread_box.insert(END, f"\n\n{err}", "error")
            self.thread_box.config(state=DISABLED)
            self.thread_box.see(END)

    # display current message history in thread_box
    def update_thread_box(self):
        self.thread_box.config(state=NORMAL) # enable editing text in thread_box
        self.thread_box.delete("1.0", END)
        self.slice_index = self.get_slice_index()
        cur_message_index = "0.0"
        for entry in self.history:
            role = entry["role"]
            content = entry["content"]
            # messages above blue horizontal slice line were not sent in prior API call
            if self.history.index(entry) == self.slice_index:
                self.thread_box.window_create("end", window=Canvas(self.thread_box, width=self.thread_box.winfo_width()-1, height=1, bg="#66f", highlightthickness=0))
            if role == "assistant":
                cur_message_index = self.thread_box.index(END)
            self.thread_box.insert(END, "\n\n---\n\n", "system") # triple dash for markdown formatting
            self.thread_box.insert(END, f"{content}", role)
        extra_lines = "" if self.thread_box.index(END) == "2.0" else "\n\n" # no extra formmatting lines above prompt if thread empty
        self.thread_box.insert(END, f"{extra_lines}{self.prompt}", "prompt")
        self.thread_box.config(state=DISABLED) # disable editing text in thread_box
        # move view to show beginning of most recent AI response
        self.thread_box.yview_moveto(int(cur_message_index.split('.')[0]) / int(self.thread_box.index(END).split('.')[0]))
        # self.thread_box.see(cur_message_index)
        
    # slice long threads before API call
    def get_slice_index(self):
        token_lengths = [len(self.encoding.encode(entry["content"])) for entry in self.history]
        while sum(token_lengths) + len(self.prompt) > self.max_tokens:
            token_lengths.pop(0)
        return len(self.history) - len(token_lengths)

    # Shift-Return
    def input_newline(self, event=None):
        self.input_box.insert(INSERT, "\n")
        return "break"

    # Ctrl-E
    def toggle_box_focus(self, event=None):
        if self.focus_get() == self.input_box:
            self.thread_box.focus_set()
        else:
            self.input_box.focus_set()
        
    # Key-Press, Key-Release
    # dynamically resize input_box while typing or resizing window
    def resize_input(self, event=None):
        num_lines = 0
        for line in self.input_box.get("1.0", "end").splitlines():
            num_lines += 1 + int(self.font.measure(line) / self.input_width)
        self.input_box.config(height=min(num_lines, 20))
        self.input_box.see(INSERT)

    # clarify caret location
    def toggle_bg_colour(self, box, event=None):
        if event.type == "9": # <FocusIn>
            box.config(background="#0b0b0b")
        elif event.type == "10": # <FocusOut>
            box.config(background="#000")

    #---------------#
    # Search Window #
    #---------------#

    # Ctrl-F
    def toggle_search_window(self, event=None):
        if not self.search_window_attributes: # set default attributes
            self.search_window_attributes["position"] = f"+{int(self.winfo_rootx() + self.winfo_width() / 2)}+{int(self.winfo_rooty() + self.winfo_height() / 2)}" # center window
            self.search_window_attributes["history"] = False # search only in this file
            self.search_window_attributes["backwards"] = False # search forwards
            self.search_window_attributes["query"] = "" # empty search string
        if self.search_window: # do not make new search window if one already exists
            self.search_window.search_entry.focus_set()
        else:
            search_window = SearchWindow(self, self.search_window_attributes)
            self.search_window = search_window

    def find_next_string(self, query_string, starting_index, backwards=False):
        first_char_index = None
        last_char_index = None
        first_char_index = self.thread_box.search(query_string, starting_index, nocase=True, backwards=backwards)
        if first_char_index: # add highlighting on matches
            self.thread_box.tag_remove("highlight", "1.0", END)
            last_char_index = f"{first_char_index}+{len(query_string)}c"
            self.thread_box.tag_add("highlight", first_char_index, last_char_index)
            self.thread_box.see(first_char_index)
        return first_char_index

    #--------------------#
    # Title and filename #
    #--------------------#
            
    # Ctrl-S
    def rename_thread(self, event=None):
        old_filename = self.filename
        new_filename = askstring("Rename Conversation", "")
        if new_filename:
            # check for duplicates
            existing_files = [f.rsplit(".", 1)[0] for f in os.listdir("history")]
            i = 2 # duplicate_filename_2, _3, _4, ...
            while new_filename in existing_files:
                new_filename = f"{new_filename.rsplit('_', 1)[0]}_{i}"
                i += 1
            # rename file and update menu
            os.rename(f"history/{old_filename}.json", f"history/{new_filename}.json")
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
        self.populate_prompt_menu()
        self.populate_history_menu(self.filename_list)
        self.title(self.engine)
        self.update_thread_box()

    def update_title(self, filename):
        file_size = round(os.path.getsize(f"history/{filename}.json") / 1024, 1)
        self.title(f"{filename} ({file_size} KB)") # tkinter window title

    def save_file(self):
        with open(f"history/{self.filename}.json", "w") as f:
            json.dump(self.history, f)
        self.update_title(self.filename)

    def load_file(self, filename):
        with open(f"history/{filename}.json", "r") as f:
            self.history = json.load(f)
        self.filename_list = self.get_history_filenames("history", ".json")
        self.filename = filename
        self.update_thread_box()
        self.update_title(filename)

    #----------------#
    # Preprompt menu #
    #----------------#

    def get_preprompts(self, prompt_file):
        with open(prompt_file, "r") as f:
            data = json.load(f)
        prompts = {}
        prompts["default"] = {
            "title": data["default"]["title"],
            "prompt": data["default"]["prompt"]
        }
        custom_prompts = []
        for p in data["custom"]:
            custom_prompts.append({"title": p["title"], "prompt": p["prompt"]})
        prompts["custom"] = custom_prompts
        return prompts
    
    def set_prompt(self, title="Default"):
        for p in self.prompt_list["custom"]:
            if p["title"] == title:
                self.prompt = p["prompt"]
                break
        if title == "Default":
            self.prompt = self.prompt_list["default"]["prompt"]
        self.thread_box.tag_remove("prompt", "1.0", END)
        self.thread_box.insert(END, f"\n\n{self.prompt}", "prompt")
        for i in range(self.prompt_menu.index(END) + 1):
            self.prompt_menu.entryconfig(i, label=self.prompt_menu.entrycget(i, "label").replace("> ", ""))
        self.prompt_menu.entryconfig(title, label="> " + title) # point to current prompt in menu
        self.update_thread_box()

    def populate_prompt_menu(self):
        self.menu.delete("Preprompts")
        self.prompt_menu.delete(0, END)
        cur_menu = self.prompt_menu
        cur_menu.add_command(label="Default", command=lambda: self.set_prompt()) # set default prompt on click
        for p in self.prompt_list["custom"]:
            title = p["title"]
            prompt = p["prompt"]
            cur_menu.add_command(label=title, command=lambda t=title: self.set_prompt(t)) # set custom prompt on click
        self.menu.add_cascade(label="Preprompts", menu=self.prompt_menu)

    #--------------#
    # History menu #
    #--------------#

    def get_history_filenames(self, directory, ext):
        filenames = os.listdir(f"{directory}/")
        # include only filenames with correct extension
        out_filenames = sorted([f.rsplit(".", 1)[0] for f in filenames if f.endswith(ext)], reverse=True)
        return out_filenames
    
    def populate_history_menu(self, filenames):
        self.menu.delete("Saved")
        self.menu.delete("History")
        self.save_menu.delete(0, END)
        for filename in filenames:
            file_size = round(os.path.getsize(f"history/{filename}.json") / 1024, 1)
            if re.match(r"\d{4}-\d{2}-\d{2}_\d{6}", filename): # yyyy-mm-dd_hhmmss default filename
                cur_menu = self.history_menu
            else: # custom filename
                cur_menu = self.save_menu
            filename = filename.replace(".json", "")
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
        self.x_border = round(self.winfo_width() / 6)
        self.thread_box.grid(padx=self.x_border)
        self.input_box.grid(padx=self.x_border)
        self.input_width = self.input_box.winfo_width()
        self.resize_input()

    # cleanup tkinter windows
    def on_close(self, event=None):
        if self.search_window:
            self.search_window.destroy()
        self.destroy()

if __name__ == "__main__":
    root = MainWindow()
    root.iconbitmap("icon.ico")
    root.mainloop()
