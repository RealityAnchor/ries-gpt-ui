from tkinter import *
from tkinter import simpledialog
from datetime import datetime
from json_search import get_files
import threading
import gpt_api
import tiktoken
import json
import os

class ChatBot:
    def __init__(self, master):
        self.master = master
        master.title("ChatGPT")
        master.state("zoomed")
        master.configure(bg="#222")
        
        self.preprompt = "Be clear and accurate. When listing items, do not describe them. When writing code, include only new, changed, or deleted lines and specify which is which."
        self.engine = "gpt-3.5-turbo"
        self.history = [{"role": "system", "content": self.preprompt}]
        self.encoding = tiktoken.encoding_for_model(self.engine)
        self.max_tokens = 3000 # 4096 - max_tokens = floor of maximum response length
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        self.history_menu_var = StringVar()
        self.history_menu_var.set("History")

        self.border_size = 8
        self.chat_box = Text(master, wrap=WORD, fg="#555", bg="#000", font=("Arial", 14), state=DISABLED, insertbackground="#975")
        self.chat_box.bind("<FocusIn>", lambda event, box=self.chat_box: self.toggle_bg_colour(box, event))
        self.chat_box.bind("<FocusOut>", lambda event, box=self.chat_box: self.toggle_bg_colour(box, event))
        self.chat_box.grid(row=0, column=0, sticky=N+S+E+W, padx=self.border_size, pady=self.border_size)
        self.chat_box.tag_configure("user", foreground="#555")
        self.chat_box.tag_configure("bot", foreground="#975")
        self.chat_box.tag_configure("system", foreground="#66f")
        self.chat_box.tag_configure("highlight", background="#66f", foreground="#000")
        
        self.input_box = Text(master, wrap=WORD, height=1, fg="#555", bg="#000", font=("Arial", 14), insertbackground="#975")
        self.input_box.bind("<FocusIn>", lambda event, box=self.input_box: self.toggle_bg_colour(box, event))
        self.input_box.bind("<FocusOut>", lambda event, box=self.input_box: self.toggle_bg_colour(box, event))
        self.input_box.grid(row=1, column=0, sticky=N+S+E+W, padx=self.border_size, pady=(0,self.border_size))
        self.input_box.focus_set()
        self.selected_box = self.input_box

        # KEYBOARD SHORTCUTS
        self.input_box.bind("<Shift-Return>", self.input_newline)
        self.input_box.bind("<Return>", self.send_message)
        self.input_box.bind("<KeyRelease>", self.resize_input)
        master.bind('<Control-e>', self.toggle_box_focus)
        master.bind('<Control-f>', self.find_string)
        master.bind('<Control-h>', self.history_filter)
        master.bind('<F5>', self.new_conversation)

        master.option_add('*Menu*activeBackground', '#333')
        master.option_add('*Menu*activeForeground', '#975')
        master.option_add('*Menu*background', '#000')
        master.option_add('*Menu*foreground', '#975')
        
        self.history_menu = Menu(master, background='#333', foreground='#FFF', activebackground='#555', activeforeground='#FFF')
        self.menu = Menu(master, background='#333', foreground='#FFF', activebackground='#555', activeforeground='#FFF')
        self.new_conversation()

        master.config(menu=self.menu)
        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=0)

    def gpt_call(self, engine, history):
        response = gpt_api.call(engine, history)
        out_content = response["choices"][0]["message"]["content"]
        re_tokens = response["usage"]["total_tokens"]
        self.history.append({"role": "assistant", "content": out_content})
        self.save_history()
        self.master.after(0, self.update_display)

    def toggle_bg_colour(self, box, event=None):
        if event.type == "9": 
            box.config(background="#111")
            self.selected_box = box
        elif event.type == "10": 
            box.config(background="#000")

    def toggle_box_focus(self, event=None):
        if self.selected_box == self.input_box:
            self.selected_box = self.chat_box
            self.chat_box.focus_set()
        elif self.selected_box == self.chat_box:
            self.selected_box = self.input_box
            self.input_box.focus_set()
        
    def resize_input(self, event=None):
        num_lines = int(self.input_box.index('end-1c').split('.')[0])
        self.input_box.config(height=min(num_lines, 12))
        
    def input_newline(self, event=None):
        self.input_box.insert(INSERT, '\n')
        return "break"
        
    def send_message(self, event=None):
        in_content = f'{self.input_box.get("1.0", "end").strip()}'
        self.input_box.config(height=1)
        self.input_box.delete("1.0", END)
        self.input_box.update_idletasks()
        
        self.history.append({"role": "user", "content": in_content})
        self.save_history()
        self.update_display()
        
        token_lengths = [len(self.encoding.encode(entry["content"])) for entry in self.history]
        while sum(token_lengths) > self.max_tokens:
            print(token_lengths.pop(0))

        n = len(token_lengths)
        sliced_history = self.history[-n:]
        t = threading.Thread(target=self.gpt_call, args=(self.engine, sliced_history))
        t.start()
        return "break"

    # HISTORY FUNCTIONS
    
    def update_title(self, file):
        file_size = round(os.path.getsize(file.name) / 1024, 1)
        self.master.title(f"{file.name} ({file_size} KB)")

    def new_conversation(self, event=None):
        self.history = [{"role": "system", "content": self.preprompt}]
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        self.json_files = [f for f in os.listdir('history/') if f.startswith("history_")]
        self.populate_history(self.json_files)
        self.update_display()
        
    def save_history(self):
        with open(f'history/history_{self.timestamp}.json', 'w') as f:
            json.dump(self.history, f)
        self.update_title(f)

    def load_history(self, filename):
        with open(f'history/{filename}', 'r') as f:
            self.history = json.load(f)
        self.json_files = [f for f in os.listdir('history/') if f.startswith("history_")]
        self.populate_history(self.json_files)
        self.update_display()
        self.update_title(f)

    def update_display(self):
        self.chat_box.config(state=NORMAL)
        self.chat_box.delete("1.0", END)
        for entry in self.history:
            role = entry["role"]
            content = entry["content"]
            if role == "system":
                self.chat_box.insert(END, f"{content}", "system")
            elif role == "user":
                self.chat_box.insert(END, f"\n\n{content}", "user")
            elif role == "assistant":
                self.chat_box.insert(END, f"\n\n{content}", "bot")
        self.chat_box.config(state=DISABLED)
        self.chat_box.see(END)

    # CTRL-F
    def find_string(self, event=None):
        query = simpledialog.askstring("Find String", "")
        if query:
            index = "1.0"
            first_match_index = None
            while True:
                index = self.chat_box.search(query, index, nocase=True, stopindex=END)
                if not index:
                    break
                end_index = f"{index}+{len(query)}c"
                self.chat_box.tag_add("highlight", index, end_index)
                if first_match_index is None:
                    first_match_index = index
                index = end_index
            if first_match_index is not None:
                self.chat_box.see(first_match_index)

    # CTRL-H
    # searches json files for a string
    def history_filter(self, event=None):
        query = simpledialog.askstring("History Filter", "")
        if query:
            matching_files = get_files(f'{os.getcwd()}/history', query)
            if matching_files:
                self.populate_history(matching_files)
        else:
            self.populate_history(self.json_files)

    def populate_history(self, files):    
        self.history_menu.delete(0, END)
        for f in sorted(files, reverse=True):
            file_size = round(os.path.getsize(f'history/{f}') / 1024, 1)
            self.history_menu.add_command(label=f"{f} ({file_size} KB)", command=lambda hf=f: self.load_history(hf))
        self.menu.delete(0, END)
        self.menu.add_cascade(label=f"History ({len(files)})", menu=self.history_menu)

root = Tk()
my_gui = ChatBot(root)
root.mainloop()
