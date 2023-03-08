from tkinter import *
from tkinter import simpledialog
from datetime import datetime
from json_search import get_filenames
import threading
import gpt_api
import tiktoken
import json
import os
import re

class ChatBot:
    def __init__(self, master):
        self.master = master
        master.title("ChatGPT")
        master.state("zoomed")
        master.configure(bg="#222")

        self.preprompt = "Be clear and accurate. When listing items, do not describe them. When writing code, include only the lines you add, delete, or change."
        self.engine = "gpt-3.5-turbo"
        self.history = [{"role": "system", "content": self.preprompt}]
        self.encoding = tiktoken.encoding_for_model(self.engine)
        self.max_tokens = 3000 # 4096 - max_tokens = floor of maximum response length
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        self.filename = self.timestamp
        
        self.border_size = 8
        self.thread_box = Text(master, wrap=WORD, fg="#555", bg="#000", font=("Arial", 14), state=DISABLED)
        self.thread_box.bind("<FocusIn>", lambda event, box=self.thread_box: self.toggle_bg_colour(box, event))
        self.thread_box.bind("<FocusOut>", lambda event, box=self.thread_box: self.toggle_bg_colour(box, event))
        self.thread_box.grid(row=0, column=0, sticky=N+S+E+W, padx=self.border_size, pady=self.border_size)
        self.thread_box.tag_configure("user", foreground="#555")
        self.thread_box.tag_configure("bot", foreground="#975")
        self.thread_box.tag_configure("system", foreground="#66f")
        self.thread_box.tag_configure("highlight", background="#66f", foreground="#000")

        self.input_box = Text(master, wrap=WORD, height=1, fg="#888", bg="#000", font=("Arial", 14), insertbackground="#888", undo=True)
        self.input_box.bind("<FocusIn>", lambda event, box=self.input_box: self.toggle_bg_colour(box, event))
        self.input_box.bind("<FocusOut>", lambda event, box=self.input_box: self.toggle_bg_colour(box, event))
        self.input_box.grid(row=1, column=0, sticky=N+S+E+W, padx=self.border_size, pady=(0,self.border_size))
        self.input_box.focus_set()
        
        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=0)

        # KEYBOARD SHORTCUTS
        self.input_box.bind("<Return>", self.send_message)
        self.input_box.bind("<Shift-Return>", self.input_newline)
        self.input_box.bind("<KeyRelease>", self.resize_input)
        master.bind('<Control-e>', self.toggle_box_focus)
        master.bind('<Control-f>', self.find_string)
        master.bind('<Control-h>', self.history_filter)
        master.bind('<Control-s>', self.rename_thread)
        master.bind('<F5>', self.new_conversation)
        master.bind('<F11>', self.toggle_fullscreen)

        master.option_add('*Menu*activeBackground', '#333')
        master.option_add('*Menu*activeForeground', '#975')
        master.option_add('*Menu*background', '#000')
        master.option_add('*Menu*foreground', '#975')

        self.menu = Menu(master, background='#333', foreground='#FFF', activebackground='#555', activeforeground='#FFF')
        self.history_menu = Menu(master, background='#333', foreground='#FFF', activebackground='#555', activeforeground='#FFF', tearoff=0)
        self.fav_menu = Menu(master, background='#333', foreground='#FFF', activebackground='#555', activeforeground='#FFF', tearoff=0)
        master.config(menu=self.menu)
        
        self.new_conversation()

    def gpt_call(self, engine, history):
        response = gpt_api.call(engine, history)
        out_content = response["choices"][0]["message"]["content"]
        re_tokens = response["usage"]["total_tokens"]
        self.history.append({"role": "assistant", "content": out_content})
        self.save_file()
        self.master.after(0, self.update_display)

    # Return
    def send_message(self, event=None):
        in_content = f'{self.input_box.get("1.0", "end").strip()}'
        self.input_box.config(height=1)
        self.input_box.delete("1.0", END)
        self.input_box.update_idletasks()
        self.history.append({"role": "user", "content": in_content})
        self.save_file()
        self.update_display()

        # slice oldest messages from overly long threads
        token_lengths = [len(self.encoding.encode(entry["content"])) for entry in self.history]
        while sum(token_lengths) > self.max_tokens:
            token_lengths.pop(0)
        n = len(token_lengths)
        sliced_history = self.history[-n:]

        t = threading.Thread(target=self.gpt_call, args=(self.engine, sliced_history))
        t.start()
        return "break"

    # Shift-Return
    def input_newline(self, event=None):
        self.input_box.insert(INSERT, '\n')
        return "break"

    # Ctrl-E
    def toggle_box_focus(self, event=None):
        if self.master.focus_get() == self.input_box:
            self.thread_box.focus_set()
        else:
            self.input_box.focus_set()

    # Ctrl-F
    def find_string(self, event=None):
        query = simpledialog.askstring("Find String", "")
        if query:
            index = "1.0"
            first_match_index = None
            while True:
                index = self.thread_box.search(query, index, nocase=True, stopindex=END)
                if not index:
                    break
                end_index = f"{index}+{len(query)}c"
                self.thread_box.tag_add("highlight", index, end_index)
                if first_match_index is None:
                    first_match_index = index
                index = end_index
            if first_match_index is not None:
                self.thread_box.see(first_match_index)

    # Ctrl-H
    # searches json files for a string
    def history_filter(self, event=None):
        query = simpledialog.askstring("History Filter", "")
        if query:
            matching_filenames = get_filenames(f'history', query)
            if matching_filenames:
                self.populate_history(matching_filenames)
        else:
            self.populate_history(self.json_files)
            
    # Ctrl-S
    def rename_thread(self, event=None):
        old_filename = self.filename
        new_filename = simpledialog.askstring("Rename Conversation", "")
        if new_filename:
            # check for duplicates
            existing_files = [f.rsplit(".", 1)[0] for f in os.listdir('history')]
            i = 2
            while new_filename in existing_files:
                new_filename = f"{new_filename.rsplit('_', 1)[0]}_{i}"
                i += 1

            # rename file and update menu
            os.rename(f"history/{old_filename}.json", f"history/{new_filename}.json")
            self.filename = new_filename
            self.save_file()
            self.json_files = self.load_json_filenames('history')
            self.populate_history(self.json_files)

    # F5
    def new_conversation(self, event=None):
        self.history = [{"role": "system", "content": self.preprompt}]
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        self.filename = self.timestamp
        self.json_files = self.load_json_filenames('history')
        self.populate_history(self.json_files)
        self.update_display()

    # F11
    def toggle_fullscreen(self, event=None):
        self.master.attributes('-fullscreen', not self.master.attributes('-fullscreen'))

    # Key-Release
    def resize_input(self, event=None):
        num_lines = int(self.input_box.index('end-1c').split('.')[0])
        self.input_box.config(height=min(num_lines, 12))


    def toggle_bg_colour(self, box, event=None):
        if event.type == "9": # <FocusIn>
            box.config(background="#111")
        elif event.type == "10": # <FocusOut>
            box.config(background="#000")

    def update_title(self, filename):
        file_size = round(os.path.getsize(f'history/{filename}.json') / 1024, 1)
        self.master.title(f"{filename} ({file_size} KB)")

    def save_file(self):
        with open(f'history/{self.filename}.json', 'w') as f:
            json.dump(self.history, f)
        self.update_title(self.filename)

    def load_file(self, filename):
        with open(f'history/{filename}.json', 'r') as f:
            self.history = json.load(f)
        self.json_files = self.load_json_filenames('history')
        self.filename = filename
        self.populate_history(self.json_files)
        self.update_display()
        self.update_title(filename)

    def load_json_filenames(self, directory):
        return [file for file in os.listdir(f'{directory}/') if file.endswith(".json")]

    def update_display(self):
        self.thread_box.config(state=NORMAL)
        self.thread_box.delete("1.0", END)
        for entry in self.history:
            role = entry["role"]
            content = entry["content"]
            if role == "system":
                self.thread_box.insert(END, f"{content}", "system")
            elif role == "user":
                self.thread_box.insert(END, f"\n\n{content}", "user")
            elif role == "assistant":
                self.thread_box.insert(END, f"\n\n{content}", "bot")
        self.thread_box.config(state=DISABLED)
        self.thread_box.see(END)

    def populate_history(self, filename_list):
        self.history_menu.delete(0, END)
        self.fav_menu.delete(0, END)
        history_count = 0
        fav_count = 0
        for filename in sorted(filename_list, reverse=True):
            file_size = round(os.path.getsize(f'history/{filename}') / 1024, 1)
            if re.match(r'\d{4}-\d{2}-\d{2}_\d{6}', filename):
                menu = self.history_menu
                history_count += 1
            else:
                menu = self.fav_menu
                fav_count += 1
            filename = filename.replace('.json', '')
            menu.add_command(label=f"{filename} ({file_size} KB)", command=lambda name=filename: self.load_file(name))
        self.menu.delete(0, END)
        self.menu.add_cascade(label=f"History ({history_count})", menu=self.history_menu)
        self.menu.add_cascade(label=f"Favourites ({fav_count})", menu=self.fav_menu)

root = Tk()
my_gui = ChatBot(root)
root.mainloop()
