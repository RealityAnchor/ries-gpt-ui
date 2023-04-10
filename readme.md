# GPT Desktop Chatbot
Python tkinter desktop chat interface for GPT via OpenAI's API

## Author
Adam Ries

Calgary, Alberta, Canada

adamalexanderries{}gmail{}com

## Features
- thread autosaving in local `history/` folder
- search current or all threads `ctrl-f`
- manually rename conversations `ctrl-s`
- preprompt dropdown menu
- [keyboard controls](#hotkeys)

## Setup
- Dependencies (older versions are for Windows 7 compatibility, because I'm a dinosaur)
  - Python 3.8.0
  - OpenAI 0.27.0
  - TikToken 0.3.0

- Set `OPENAI_API_KEY` in your environment variables
  - [Get an API key here.](https://platform.openai.com/account/api-keys)
  - `import openai` automatically finds your key if you've set it to that name

- run main_window.py

## Project Directory

### main_window.py
![main_window](screenshots/main_window.png)
- three dropdown menus
  - `Preprompts` - select system message
  - `Saved`, `History` - load threads
- thread box contains current conversation history
  - assistant: gold #997755
  - user: grey #555555
  - system: blue #6666ff
  - error: red #ff0000
- input box below
- threads are truncated if longer than max_tokens
  - currently hardcoded 3096 leaving 1000 tokens for response
  - blue horizontal line shows where previous API call sliced thread

### search_window.py
![search_window](screenshots/search_window.png)

### gpt.py
- separated from main_window.py because it kept trying to correct itself after OpenAI changed [API formatting](https://platform.openai.com/docs/guides/chat) from `Completion` to `ChatCompletion` on 2023-03-01 with `gpt-3.5-turbo` release (due to 2021 training data cutoff)
- run this by itself for barebones interaction with GPT in terminal

### history/
- threads saved in this folder as json files
- open old threads with `History` and `Saved` dropdown menus
![history menu](screenshots/history_menu.png)

Format:
- 2023-03-02_151106.json (`datetime.now().strftime("%Y-%m-%d_%H%M%S")`)
- [{"role": "user", "content": "user input"}, {"role": "assistant", "content": "AI response"}, ...]

### preprompts.json
![preprompts](screenshots/preprompts.png)
- inserted before each API call as `{"role": "system", "content": "[preprompt text]"}`
- not saved in conversation history
- add/remove/edit manually for now (any text editor)

Included preprompts:
- Default: Be accurate, detailed, and clear. Predict my needs.
- Coder: You are a senior software developer and mentor. I am a novice developer and student.
- Socrates: Reply in the Socratic style. Do not provide answers. Instead, patiently and methodically ask questions such that curious minds may lead themselves to truth and wisdom. When appropriate you may break down topics into ever-finer detail, or broaden the scope, or make insightful lateral leaps.
- Cthulu: Reply in horrific Lovecraftian style. You are an eldritch god, whose words are dredged from an unfathomable cosmic abyss.
- Poet: Write beautifully and metaphorically.

## Hotkeys
Main window:
- `ctrl-e` toggle focus between input box and thread box
- `ctrl-f` toggle search window
- `ctrl-s` rename current thread
- `ctrl-w` close current window
- `f5` start a new conversation thread
- `f11` toggle fullscreen
- `Return` send message
- `Shift-Return` insert newline

Search window:
- `return` next match
- `ctrl-d` toggle search direction
- `ctrl-g` toggle searching in current/all files
- `ctrl-f`, `esc` close search window