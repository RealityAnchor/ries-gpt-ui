from tkinter import *
import openai
import threading
from datetime import datetime
import json
import os

class ChatBot:
    def __init__(self, master):
        self.master = master
        master.title("ChatGPT")
        master.configure(bg="#000")
        
        self.preprompt = "Prioritize accuracy, clarity, eloquence, and brevity. Ask questions to clarify ambiguity or introduce ideas I seem not to know about."
        self.engine = "gpt-3.5-turbo"
        master.state("zoomed")
        
        self.history = [{"role": "system", "content": self.preprompt}]

        self.history_dir = 'history/'
        self.history_file = f"{self.history_dir}history_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
        self.save_history()

        self.history_json_files = sorted([f for f in os.listdir(self.history_dir) if f.startswith("history_")])
        self.history_menu_var = StringVar()
        self.history_menu_var.set("History")
        
        
        self.chat_box = Text(master, wrap=WORD, width=80, height=20, fg="#555", bg="#000", font=("Arial", 14))
        self.chat_box.grid(row=0, column=0, sticky=N+S+E+W)
        self.chat_box.tag_configure("user", foreground="#555")
        self.chat_box.tag_configure("bot", foreground="#997755")
        self.chat_box.tag_configure("system", foreground="#FFFF00")

        self.input_box = Text(master, wrap=WORD, width=80, height=1, fg="#888", bg="#333", font=("Arial", 14))
        self.input_box.grid(row=1, column=0, sticky=N+S+E+W, pady=20)
        self.input_box.bind("<Shift-Return>", self.insert_line)
        self.input_box.bind("<KeyRelease>", self.resize_input_box)
        self.input_box.bind("<Return>", self.send_message)
        self.input_box.focus_set()

        # Create menu bar
        menu = Menu(master)
        history_menu = Menu(menu, tearoff=0)

        for history_file in self.history_json_files:
            file_size = os.path.getsize(f'history/{history_file}') // 1024
            history_menu.add_command(label=f"{history_file} ({file_size} KB)", command=lambda hf=history_file: self.load_history(hf))

        menu.add_cascade(label="History", menu=history_menu)

        master.config(menu=menu)

        # Create text area and input box widgets
        self.chat_box = Text(master, wrap=WORD, width=80, height=20, fg="#555", bg="#000", font=("Arial", 14))
        self.chat_box.grid(row=0, column=0, sticky=N+S+E+W)
        self.chat_box.tag_configure("user", foreground="#555")
        self.chat_box.tag_configure("bot", foreground="#997755")
        self.chat_box.tag_configure("system", foreground="#FFFF00")

        self.input_box = Text(master, wrap=WORD, width=80, height=1, fg="#888", bg="#333", font=("Arial", 14))
        self.input_box.grid(row=1, column=0, sticky=N+S+E+W, pady=20)
        self.input_box.bind("<Shift-Return>", self.insert_line)
        self.input_box.bind("<KeyRelease>", self.resize_input_box)
        self.input_box.bind("<Return>", self.send_message)
        self.input_box.focus_set()

        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=0)

        # Style the menu bar
        master.option_add('*Menu*activeBackground', '#333')
        master.option_add('*Menu*activeForeground', '#FFF')
        master.option_add('*Menu*background', '#333')
        master.option_add('*Menu*foreground', '#FFF')
        master.bind('<Alt_L>', lambda event: menu.focus_set())

        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)
        
    def save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f)

    def load_history(self, filename):
        with open(self.history_dir + filename, 'r') as f:
            self.history = json.load(f)
        self.display_history()
        
    def insert_line(self, event):
        self.input_box.insert(INSERT, "\n")
        return "break"

    def resize_input_box(self, event):
        lines = self.input_box.get("1.0", "end-1c").split("\n")
        self.input_box.config(height=len(lines))
        
    def send_message(self, event):
        in_content = f'{self.input_box.get("1.0", "end").strip()}'
        self.input_box.config(height=1)
        self.input_box.delete("1.0", END)
        self.input_box.update_idletasks()

        self.history.append({"role": "user", "content": in_content})
        self.save_history()

        # Create a new thread to run the GPT method
        t = threading.Thread(target=self.get_response, args=(self.engine, self.history))
        t.start()

    def get_response(self, engine, history):
        # Call the GPT method to get a response from the OpenAI API
        response = self.GPT(engine, history)
        out_content = response["choices"][0]["message"]["content"]
        self.history.append({"role": "assistant", "content": out_content})
        self.save_history()

        # Update the chat history in the main thread
        self.master.after(0, self.display_history)

    def GPT(self, engine, history):
        return openai.ChatCompletion.create(
                model = engine,
                messages = history
            )

    def display_history(self):
        self.chat_box.delete("1.0", END)
        for entry in self.history:
            role = entry["role"]
            content = entry["content"]
            if role == "system":
                self.chat_box.insert(END, f"PREPROMPT = [{content}]\n\n", "system")
            elif role == "user":
                self.chat_box.insert(END, f"{content}\n\n", "user") # how to display > at start of each newline
            elif role == "assistant":
                self.chat_box.insert(END, f"{content}\n\n", "bot")
        self.chat_box.see(END)


root = Tk()
my_gui = ChatBot(root)
root.mainloop()
