# To Do

## Chores
* Fix redundant language in social media preview
* Update history menu without restarting

## Features
* Slice messages partway through if over 3k tokens
* Use grid instead of recalculating border for dynamic horizontal spacing
* Re-implement counting menu items
* Help button ctrl-h
* Ctrl-up/down, snap to prompts, up-down always navigate one line
* When output arrives, .see to answer start
* Responsive web design for phone/desktop online app
* Whisper/elevenlabs for speech i/o
* Blank string message = resend last message
* Ctrl-n new tab, ctrl-left/right tab switching
* Token limit
    * 3-way toggle prompt/response pairs to force-include, force-disclude, or be ambivalent
* Code editing mode
    * Code-specific preprompt
    * Read code from file, always send as first message
    * Codex model "handles whitespace more efficiently"
* Add preprompt and timestamp to history JSON files
* Options JSON file?
* Drag inner window to adjust width or toggle narrow/wide for reading/coding
* Field to set API key within app
* Custom keybinds, options (JSON?)
* Lock vertical position toggle
* Copy button beside responses and/or codeblocks

## GPT-4
* Image input
* Plugins

## SearchWindow class
* Clear search button
* Label with query inside menu bar when searching files
* Handle special characters in filenames (apostrophes, ...)
* Tag search field + content search field
* Optimization
    * Stop file search after first match

## PromptEditor class
* Preprompt as title to right of input
* Click on title (ctrl-p):
    * See current preprompt
    * See list of options
    * Edit/create

## Sorting conversations
* "Chapters" in left column, numbered by prompt-response pair
* Delete, hide, click-drag
* Saved files by recently-edited first
* Collapse/expand responses
* Visual/tree/folder structure, separate window
* Replace "Saved" with tags (include or disclude), static date+time filename
* Table with columns: time created, time modified, filesize, thread length, tags
* Categories of dropdown boxes
* Automatic renaming via LLM
* Look only at prompts, ignore responses
* Merge, revert to timestamp

## Dependencies
* Linux dual boot -> Py 3.11

## Unit testing

## Packaging
