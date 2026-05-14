# press-skill

Simple desktop auto key presser built with Tkinter.

## Features

- Choose a single key to auto-press
- Set press interval in seconds
- Start/stop from UI buttons
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
