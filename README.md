# press-skill

Simple desktop key automation app built with Tkinter.

## Features

- Choose a single key to send
- Set press interval in seconds
- Target a window by part of its title
- Briefly focus the target window, press the key, and restore the previous focus
- Global hotkey `F8` to toggle start/stop

## Requirements

- Python 3.11+
- Windows (tested flow uses global keyboard hooks)

## Install

```powershell
uv sync
```

## Run

```powershell
uv run python main.py
```

## Notes

- Run terminal as Administrator if global hotkeys do not register.
- Only single-character keys are currently supported.
- The window match uses the first visible window whose title contains the text you entered.
