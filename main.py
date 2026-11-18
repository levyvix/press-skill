import threading
import tkinter as tk
from tkinter import messagebox

import keyboard
from pynput.keyboard import Controller


class AutoPressApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Auto Key Presser")
        self.root.geometry("360x220")
        self.root.resizable(False, False)

        self.running = False
        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.controller = Controller()

        self.key_var = tk.StringVar(value="e")
        self.interval_var = tk.StringVar(value="25")
        self.status_var = tk.StringVar(value="Status: Stopped")

        self._build_ui()
        keyboard.add_hotkey("F1", lambda: self.root.after(0, self.toggle_running))

    def _build_ui(self) -> None:
        frame = tk.Frame(self.root, padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Key to press:").grid(row=0, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.key_var, width=12).grid(
            row=0, column=1, sticky="w", padx=8
        )

        tk.Label(frame, text="Interval (seconds):").grid(
            row=1, column=0, sticky="w", pady=(10, 0)
        )
        tk.Entry(frame, textvariable=self.interval_var, width=12).grid(
            row=1, column=1, sticky="w", padx=8, pady=(10, 0)
        )

        btn_row = tk.Frame(frame)
        btn_row.grid(row=2, column=0, columnspan=2, pady=16, sticky="w")
        tk.Button(btn_row, text="Start", width=10, command=self.start).pack(side="left")
        tk.Button(btn_row, text="Stop", width=10, command=self.stop).pack(
            side="left", padx=(8, 0)
        )

        tk.Label(frame, textvariable=self.status_var).grid(
            row=3, column=0, columnspan=2, sticky="w"
        )
        tk.Label(frame, text="Global stop hotkey: F1").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )

    def start(self) -> None:
        if self.running:
            return

        key = self.key_var.get().strip()
        normalized_key = key.lower()
        if len(normalized_key) != 1:
            messagebox.showerror("Invalid key", "Please provide a single key (example: x).")
            return

        try:
            interval = float(self.interval_var.get().strip())
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid interval", "Interval must be a number greater than 0."
            )
            return

        self.running = True
        self.stop_event.clear()
        self.status_var.set(f"Status: Running ({normalized_key} every {interval}s)")
        self.worker = threading.Thread(
            target=self._run_presser, args=(normalized_key, interval), daemon=True
        )
        self.worker.start()

    def stop(self) -> None:
        self.running = False
        self.stop_event.set()
        self.root.after(0, lambda: self.status_var.set("Status: Stopped"))

    def toggle_running(self) -> None:
        if self.running:
            self.stop()
            return
        self.start()

    def _run_presser(self, key: str, interval: float) -> None:
        while not self.stop_event.is_set():
            self.controller.press(key)
            self.controller.release(key)
            if self.stop_event.wait(interval):
                break


def main() -> None:
    root = tk.Tk()
    app = AutoPressApp(root)
    root.protocol(
        "WM_DELETE_WINDOW",
        lambda: (app.stop(), keyboard.unhook_all_hotkeys(), root.destroy()),
    )
    root.mainloop()


if __name__ == "__main__":
    main()
