from tkinter import *
from tkinter import simpledialog
from chatgpt import GPT
from datetime import datetime
from json_search import get_files
import threading
import json
import os

class ChatBot:
    def __init__(self, master):
        self.master = master
        master.title("ChatGPT")
        master.state("zoomed")
        master.configure(bg="#000")
        master.bind('<F5>', self.new_conversation)
        master.bind('<Control-f>', self.filter_history)
        
        self.preprompt = "Prioritize accuracy, clarity, eloquence, and brevity. Ask questions and suggest interesting ideas when appropriate."
        self.history = [{"role": "system", "content": self.preprompt}]
        self.engine = "gpt-3.5-turbo"
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        self.history_menu_var = StringVar()
        self.history_menu_var.set("History")
        
        self.chat_box = Text(master, wrap=WORD, width=80, height=20, fg="#555", bg="#000", font=("Arial", 14))
        self.chat_box.grid(row=0, column=0, sticky=N+S+E+W)
        self.chat_box.tag_configure("user", foreground="#555")
        self.chat_box.tag_configure("bot", foreground="#997755")
        self.chat_box.tag_configure("system", foreground="#6666ff")

        self.input_box = Text(master, wrap=WORD, width=80, height=1, fg="#555", bg="#000", font=("Arial", 14))
        self.input_box.config(insertbackground="#888")
        self.input_box.grid(row=1, column=0, sticky=N+S+E+W, padx=8, pady=8)
        self.input_box.focus_set()
        self.input_box.bind("<Shift-Return>", self.input_newline)
        self.input_box.bind("<Return>", self.send_message)
        self.input_box.bind("<KeyRelease>", self.resize_input)

        master.option_add('*Menu*activeBackground', '#333')
        master.option_add('*Menu*activeForeground', '#997755')
        master.option_add('*Menu*background', '#000')
        master.option_add('*Menu*foreground', '#997755')
        
        self.history_menu = Menu(master, background='#333', foreground='#FFF', activebackground='#555', activeforeground='#FFF')
        self.menu = Menu(master, background='#333', foreground='#FFF', activebackground='#555', activeforeground='#FFF')
        self.new_conversation()

        master.config(menu=self.menu)
        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=0)

    def gpt_call(self, engine, history):
        response = GPT(engine, history)
        out_content = response["choices"][0]["message"]["content"]
        re_tokens = response["usage"]["total_tokens"]
        self.history.append({"role": "assistant", "content": out_content})
        self.save_history()
        self.master.after(0, self.update_display)
        
    def resize_input(self, event=None):
        num_lines = int(self.input_box.index('end-1c').split('.')[0])
        self.input_box.config(height=min(num_lines, 10))
        self.chat_box.see(END)
        
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
        t = threading.Thread(target=self.gpt_call, args=(self.engine, self.history))
        t.start()
        return "break"

    # HISTORY FUNCTIONS
    
    def update_title(self, file):
        file_size = round(os.path.getsize(file.name) / 1024, 1)
        self.master.title(f"{file.name} ({file_size} KB)")

    def new_conversation(self, event=None):
        self.history = [{"role": "system", "content": self.preprompt}]
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        self.all_json_files = sorted([f for f in os.listdir('history/') if f.startswith("history_")], reverse=True)
        self.populate_history(self.all_json_files)
        self.update_display()
        
    def save_history(self):
        with open(f'history/history_{self.timestamp}.json', 'w') as f:
            json.dump(self.history, f)
        self.update_title(f)

    def load_history(self, filename):
        with open(f'history/{filename}', 'r') as f:
            self.history = json.load(f)
        self.update_display()
        self.update_title(f)

    def update_display(self):
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
        self.chat_box.see(END)

    def filter_history(self, event=None):
        query = simpledialog.askstring("Filter History", "String:")
        if query:
            matching_files = get_files(f'{os.getcwd()}/history', query)
            if matching_files:
                self.populate_history(matching_files)
        else:
            self.populate_history(self.all_json_files)

    def populate_history(self, files):    
        self.history_menu.delete(0, END)
        for f in files:
            file_size = round(os.path.getsize(f'history/{f}') / 1024, 1)
            self.history_menu.add_command(label=f"{f} ({file_size} KB)", command=lambda hf=f: self.load_history(hf))
        self.menu.delete(0, END)
        self.menu.add_cascade(label=f"History ({len(files)})", menu=self.history_menu)

root = Tk()
my_gui = ChatBot(root)
root.mainloop()
