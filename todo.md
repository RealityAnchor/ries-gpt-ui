Fix redundant language in social media preview
Update history menu without restarting

Features
  slice messages partway through if over 3k tokens
  use grid instead of recalculating border for dynamic horizontal spacing
  re-implement counting menu items
  help button ctrl-h
  ctrl-up/down, snap to prompts, up-down always navigate one line
  when output arrives, .see to answer start
  responsive web design for phone/desktop online app
  Whisper/elevenlabs for speech i/o
  blank string message = resend last message
  ctrl-n new tab, ctrl-left/right tab switching
  token limit
    3-way toggle prompt/response pairs to force-include, force-disclude, or be ambivalent
  code editing mode
    code-specific preprompt
    read code from file, always send as first message
    codex model "handles whitespace more efficiently"
  add preprompt and timestamp to history json files
  options json file?
  drag inner window to adjust width or toggle narrow/wide for reading/coding
  field to set API key within app
  custom keybinds, options (json?)
  lock vertical position toggle
  copy button beside responses and/or codeblocks
  
GPT-4
  image input
  plugins

SearchWindow class
  clear search button
  label with query inside menu bar when searching files
  handle special characters in filenames (apostrophes, ...)
  tag search field + content search field
  optimization
    stop file search after first match
  
PromptEditor class
  preprompt as title to right of input
  click on title (ctrl-p):
    see current preprompt
    see list of options
    edit/create

Sorting conversations
  "chapters" in left column, numbered by prompt-response pair
  delete, hide, click-drag
  saved files by recently-edited first
  collapse/expand responses
  visual/tree/folder structure, separate window
  replace "Saved" with tags (include or disclude), static date+time filename
  table with columns: time created, time modified, filesize, thread length, tags
  categories of dropdown boxes
  automatic renaming via LLM
    look only at prompts, ignore responses
  merge, revert to timestamp

Dependencies
  Linux dual boot -> Py 3.11

Unit testing

Packaging