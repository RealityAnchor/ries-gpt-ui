# GPT Desktop Chatbot

tkinter desktop chat interface for interacting with GPT-3 via OpenAI's API

## Author

Adam Ries

Calgary, Alberta, Canada

adamalexanderries{}gmail{}com

## Features

- saves conversations locally in `history/`
- search feature `ctrl+f`
- preprompt dropdown menu

## Setup

Dependencies based on older versions because I'm a dinosaur still using Windows 7.

Python 3.8.0

OpenAI 0.27.0

TikToken 0.3.0

Set OPENAI_API_KEY in your environment variables.

[Get an API key here.](https://platform.openai.com/account/api-keys)

## Project Directory

### main_window.py
- run this to use program
- three dropdown menus
  - `Preprompts` to select system message (not saved with thread)
  - `Saved` and `History` to load old threads
- thread box contains current conversation history
  - assistant: gold #997755
  - user: grey #555555
  - system: blue #6666ff
  - error: red #ff0000
- input box is where user types new messages (automatically resizes up to 20 lines)
- threads are sliced off if longer than max_tokens (currently hardcoded 3096 leaving 1000 tokens for response)
  - blue horizontal line shows where **previous** API call sliced thread

### search_window.py
- text input and search button
`return` next match
`ctrl + d` toggle search direction
`ctrl + g` toggle searching in files
`ctrl + f`, `esc` close window

### gpt.py
- separated from main_window.py because it kept trying to correct itself after OpenAI changed [API formatting](https://platform.openai.com/docs/guides/chat) from `Completion` to `ChatCompletion` on 2023-03-01 with `gpt-3.5-turbo` release.
- run this by itself for barebones interaction with chatbot in terminal

### history/
- conversations saved here as json files 
- 2023-03-02_151106.json [{"role": "user", "content": "user input"}, {"role": "assistant", "content": "AI response"}, ...]
- default title formatted with `datetime.now().strftime("%Y-%m-%d_%H%M%S")`
- rename current file with `ctrl+s`

### preprompts.json
- inserted in each API call as `"role": "system"`
- edit preprompts manually for now (notepad++, VS Code, etc.)
  - Default | Be accurate, detailed, and clear. Predict my needs.
  - Coder | You are a senior software developer and mentor. I am a novice developer and student.
  - Socrates | Reply in the Socratic style. Do not provide answers. Instead, patiently and methodically ask questions such that curious minds may lead themselves to truth and wisdom. When appropriate you may break down topics into ever-finer detail, or broaden the scope, or make insightful lateral leaps.
  - Cthulu | Reply in horrific Lovecraftian style. You are an eldritch god, whose words are dredged from an unfathomable cosmic abyss.
  - Poet | Write beautifully and metaphorically.

## Hotkeys

`ctrl + e` toggle focus between input box and thread box

`ctrl + f` toggle search window

`ctrl + s` rename current thread

`ctrl + w` close current window

`f5` start a new conversation thread

`f11` toggle fullscreen

With input box focused:

  `Return` send message
  
  `Shift-Return` inserts newline without sending message

## License

MIT
