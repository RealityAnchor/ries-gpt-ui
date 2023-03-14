# built in
from datetime import datetime
import json
import os
import re
import threading

# pip install
from tkinter import *
from tkinter.simpledialog import askstring
from tkinter.font import Font
import tiktoken

# custom
from search_window import SearchWindow
import gpt


class MainWindow(Tk):
    def __init__(self):
        super().__init__()
        self.title("ChatGPT")
        self.state("zoomed")
        self.configure(bg="#222")
        
        self.prompt_list = self.get_prompts("prompts.json")
        self.prompt = self.prompt_list['default']['prompt']
        self.engine = "gpt-3.5-turbo"
        self.history = []
        self.encoding = tiktoken.encoding_for_model(self.engine)
        self.max_tokens = 3096 # 4096 - max_tokens == floor of maximum response length
        self.slice_index = 0 # only messages below blue line included in prior API call
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        self.filename = self.timestamp
        self.font = Font(family="Arial", size=14)
        self.search_window_attributes = {}
        
        self.search_window = None
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.border_size = 8
        self.thread_box = Text(self, wrap=WORD, fg="#555", bg="#000", font=self.font, state=DISABLED)
        self.thread_box.bind("<FocusIn>", lambda event, box=self.thread_box: self.toggle_bg_colour(box, event))
        self.thread_box.bind("<FocusOut>", lambda event, box=self.thread_box: self.toggle_bg_colour(box, event))
        self.thread_box.grid(row=0, column=0, sticky=N+S+E+W, padx=self.border_size, pady=self.border_size)
        self.thread_box.tag_configure("user", foreground="#555")
        self.thread_box.tag_configure("assistant", foreground="#975")
        self.thread_box.tag_configure("system", foreground="#66f")
        self.thread_box.tag_configure("prompt", foreground="#6f6")
        self.thread_box.tag_configure("highlight", background="#ff6", foreground="#000")
        self.thread_box.tag_configure("error", foreground="#f00")
            
        self.input_box = Text(self, wrap=WORD, height=1, fg="#888", bg="#000", font=self.font, insertbackground="#888", undo=True)
        self.input_box.bind("<FocusIn>", lambda event, box=self.input_box: self.toggle_bg_colour(box, event))
        self.input_box.bind("<FocusOut>", lambda event, box=self.input_box: self.toggle_bg_colour(box, event))
        self.input_box.grid(row=1, column=0, sticky=N+S+E+W, padx=self.border_size, pady=(0,self.border_size))
        self.input_box.focus_set()
        self.max_width = self.input_box.winfo_width()
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # KEYBOARD SHORTCUTS
        self.input_box.bind("<Return>", self.send_message)
        self.input_box.bind("<Shift-Return>", self.input_newline)
        self.input_box.bind("<KeyPress>", self.resize_input)
        self.input_box.bind("<KeyRelease>", self.resize_input)
        self.bind('<Configure>', self.resize_window)
        self.bind('<Control-e>', self.toggle_box_focus)
        self.bind('<Control-f>', self.open_search_window)
        self.bind('<Control-s>', self.rename_thread)
        self.bind('<F5>', self.new_conversation)
        self.bind('<F11>', self.toggle_fullscreen)

        # Menu
        self.option_add('*Menu*activeBackground', '#333')
        self.option_add('*Menu*activeForeground', '#975')
        self.option_add('*Menu*background', '#000')
        self.option_add('*Menu*foreground', '#975')
        self.menu = Menu(self, background='#333', foreground='#FFF', activebackground='#555', activeforeground='#FFF')
        self.prompt_menu = Menu(self, background='#333', foreground='#FFF', activebackground='#555', activeforeground='#FFF', tearoff=0) 
        self.history_menu = Menu(self, background='#333', foreground='#FFF', activebackground='#555', activeforeground='#FFF', tearoff=0)
        self.save_menu = Menu(self, background='#333', foreground='#FFF', activebackground='#555', activeforeground='#FFF', tearoff=0)      
        self.menu.add_cascade(label="Prompts", menu=self.prompt_menu)
        self.menu.add_cascade(label="Saved", menu=self.save_menu)
        self.menu.add_cascade(label="History", menu=self.history_menu)
        self.config(menu=self.menu)

        self.update()
        self.new_conversation()

    # Messaging
    # Return
    def send_message(self, event=None):
        in_content = f'{self.input_box.get("1.0", "end").strip()}'
        self.input_box.config(height=1)
        self.input_box.delete("1.0", END)
        self.input_box.update_idletasks()
        self.history.append({"role": "user", "content": in_content})
        self.save_file()
        self.update_thread_box()
        t = threading.Thread(target=self.invoke_gpt, args=(self.engine, self.history[self.slice_index:]))
        t.start()
        return "break"

    def invoke_gpt(self, engine, history):
        try:
            history.insert(-1, {"role": "system", "content": self.prompt})
            response = gpt.api_call(engine, history)
            history.pop(-1)
            out_content = response["choices"][0]["message"]["content"]
            self.history.append({"role": "assistant", "content": out_content})
            self.save_file()
            self.after(0, self.update_thread_box)
        except Exception as err:
            self.thread_box.config(state=NORMAL)
            self.thread_box.insert(END, f'\n\n{err}', "error")
            self.thread_box.config(state=DISABLED)
            self.thread_box.see(END)

    def update_thread_box(self):
        self.thread_box.config(state=NORMAL)
        self.thread_box.delete("1.0", END)
        self.slice_index = self.get_slice_index()
        for entry in self.history:
            role = entry["role"]
            content = entry["content"]
            if self.history.index(entry) == self.slice_index: # blue horizontal slice line
                self.thread_box.window_create("end", window=Canvas(self.thread_box, width=self.thread_box.winfo_width()-1, height=1, bg="#66f", highlightthickness=0))
            self.thread_box.insert(END, f"\n\n{content}", role)
        extra_lines = "\n\n" if len(self.history) > 1 else ""
        self.thread_box.insert(END, f"{extra_lines}{self.prompt}", "prompt")
        self.thread_box.config(state=DISABLED)
        self.thread_box.see(END)

    def get_slice_index(self):
        token_lengths = [len(self.encoding.encode(entry["content"])) for entry in self.history]
        while sum(token_lengths) + len(self.prompt) > self.max_tokens:
            token_lengths.pop(0)
        return len(self.history) - len(token_lengths)

    # Shift-Return
    def input_newline(self, event=None):
        self.input_box.insert(INSERT, '\n')
        return "break"

    # Ctrl-E
    def toggle_box_focus(self, event=None):
        if self.focus_get() == self.input_box:
            self.thread_box.focus_set()
        else:
            self.input_box.focus_set()

    # Ctrl-F
    def open_search_window(self, event=None):
        if not self.search_window_attributes:
            self.search_window_attributes['position'] = f"+{int(self.winfo_rootx() + self.winfo_width() / 2)}+{int(self.winfo_rooty() + self.winfo_height() / 2)}"
            self.search_window_attributes['history'] = False
            self.search_window_attributes['backwards'] = False
            self.search_window_attributes['query'] = ""
        if self.search_window:
            self.search_window.search_entry.focus_set()
        else:
            search_window = SearchWindow(self, self.search_window_attributes)
            self.search_window = search_window

    def find_next_string(self, query_string, starting_index, backwards=False):
        first_char_index = None
        last_char_index = None
        
        first_char_index = self.thread_box.search(query_string, starting_index, nocase=True, backwards=backwards)

        if first_char_index:
            self.thread_box.tag_remove("highlight", "1.0", END)
            last_char_index = f"{first_char_index}+{len(query_string)}c"
            self.thread_box.tag_add("highlight", first_char_index, last_char_index)
            self.thread_box.see(first_char_index)

        return first_char_index
            
    # Ctrl-S
    def rename_thread(self, event=None):
        old_filename = self.filename
        new_filename = askstring("Rename Conversation", "")
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
            self.filename_list = self.get_history_filenames('history', '.json')
            self.populate_history_menu(self.filename_list)

    # F5
    def new_conversation(self, event=None):
        self.history = []
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        self.filename = self.timestamp
        self.filename_list = self.get_history_filenames('history', '.json')
        self.populate_prompt_menu()
        self.populate_history_menu(self.filename_list)
        self.title("ChatGPT")
        self.update_thread_box()

    # F11
    def toggle_fullscreen(self, event=None):
        self.attributes('-fullscreen', not self.attributes('-fullscreen'))
        
    # Configure
    def resize_window(self, event=None):
        self.max_width = self.input_box.winfo_width()
        self.resize_input()
        
    # Key-Release
    def resize_input(self, event=None):
        num_lines = 0
        for line in self.input_box.get('1.0', 'end').splitlines():
            num_lines += 1 + int(self.font.measure(line) / self.max_width)
        self.input_box.config(height=min(num_lines, 20))

    def toggle_bg_colour(self, box, event=None):
        if event.type == "9": # <FocusIn>
            box.config(background="#111")
        elif event.type == "10": # <FocusOut>
            box.config(background="#000")

    def update_title(self, filename):
        file_size = round(os.path.getsize(f'history/{filename}.json') / 1024, 1)
        self.title(f"{filename} ({file_size} KB)")

    def save_file(self):
        with open(f'history/{self.filename}.json', 'w') as f:
            json.dump(self.history, f)
        self.update_title(self.filename)

    def load_file(self, filename):
        with open(f'history/{filename}.json', 'r') as f:
            self.history = json.load(f)
        self.filename_list = self.get_history_filenames('history', '.json')
        self.filename = filename
        self.update_thread_box()
        self.update_title(filename)

    # Prompt Menu
    
    def get_prompts(self, prompt_file):
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
        for prompt_dict in self.prompt_list['custom']:
            if prompt_dict['title'] == title:
                self.prompt = prompt_dict['prompt']
                break
        else:
            self.prompt = self.prompt_list['default']['prompt']
        self.thread_box.tag_remove("prompt", "1.0", END)
        self.thread_box.insert(END, f"\n\n{self.prompt}", "prompt")
        for i in range(self.prompt_menu.index(END) + 1):
            self.prompt_menu.entryconfig(i, label=self.prompt_menu.entrycget(i, "label").replace("> ", ""))
        self.prompt_menu.entryconfig(title, label="> " + title)
        self.update_thread_box()

    def populate_prompt_menu(self):
        self.menu.delete("Prompts")
        self.prompt_menu.delete(0, END)
        cur_menu = self.prompt_menu
        cur_menu.add_command(label="Default", command=lambda: self.set_prompt())
        for p in self.prompt_list["custom"]:
            title = p["title"]
            prompt = p["prompt"]
            cur_menu.add_command(label=title, command=lambda t=title: self.set_prompt(t))
        self.menu.add_cascade(label="Prompts", menu=self.prompt_menu)

    # History Menu

    def get_history_filenames(self, directory, ext):
        filenames = os.listdir(f'{directory}/')
        out_filenames = sorted([f.rsplit(".", 1)[0] for f in filenames if f.endswith(ext)], reverse=True)
        return out_filenames
    
    def populate_history_menu(self, filenames):
        self.menu.delete("Saved")
        self.menu.delete("History")
        self.save_menu.delete(0, END)
        for filename in filenames:
            file_size = round(os.path.getsize(f'history/{filename}.json') / 1024, 1)
            if re.match(r'\d{4}-\d{2}-\d{2}_\d{6}', filename):
                cur_menu = self.history_menu
            else:
                cur_menu = self.save_menu
            filename = filename.replace('.json', '')
            cur_menu.add_command(label=f"{filename} ({file_size} KB)", command=lambda name=filename: self.load_file(name))
        self.menu.add_cascade(label="Saved", menu=self.save_menu)
        self.menu.add_cascade(label="History", menu=self.history_menu)

    # Cleanup

    def on_close(self):
        if self.search_window:
            self.search_window.destroy()
        self.destroy()

if __name__ == "__main__":
    root = MainWindow()
    root.iconbitmap('icon.ico')
    root.mainloop()
