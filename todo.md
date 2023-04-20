# To Do

## Features
- Slice messages partway through if over 3k tokens
- Help button ctrl-h
- Ctrl-up/down, snap to prompts, up-down always navigate one line
- Responsive web design for phone/desktop online app
- Whisper/elevenlabs for speech i/o
- Blank string message = resend last message
- Ctrl-n new tab, ctrl-left/right tab switching
- Code editing mode
  - Read code from file, always send as first message
  - Codex model "handles whitespace more efficiently"
- Add preprompt and timestamp to history JSON files
- Drag inner window to adjust width or toggle narrow/wide for reading/coding
- Field to set API key within app
- Lock vertical position toggle
- Copy button beside responses and/or codeblocks
- Scrollbar

## History menu
- Update without restarting
- Make OptionMenu in left column
- Remove top menu bar
- Sort files by recently-edited
- Replace "Saved" with tags (include or disclude)
- Use only date+time for filename
  - Store thread title in json
  - Automatically generate titles with GPT
- Upgrade to history window
  - Display threads in folders in tree structure
  - Implement click-and-drag
  - Display table with columns: time created, time modified, filesize, thread length, tags

## Options menu `ctrl-o`
- Store user settings in JSON file
- Keybinds
- Font
- Colours

## SearchWindow class `ctrl-s`
- Clear search button
- Handle special characters in filenames (apostrophes, ...)
- Separate tag search field + content search field
- Optimization
  - Stop file search after first match

## PrepromptEditor class `ctrl-p`
- Show pp on hover in menu
- Implement pp editing/creation window

## Chapters
- Represent prompt-response pairs in left column, numbered
- Snap to prompt when chapter number clicked
- Display options below chapter numbers
  - Copy
  - Collapse/expand
  - Delete (and undo)
  - 3-way toggle for token limit
    - force-include
    - force-disclude
    - chronological (default)

## GitHub
- Fix redundant language in social media preview
- Implement unit testing
- Implement packaging

## GPT-4
- Image input
- Plugins

## Dependencies
- Linux dual boot -> Py 3.11