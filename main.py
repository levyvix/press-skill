import ctypes
import threading
import time
import tkinter as tk
from tkinter import messagebox

import keyboard
from pynput.keyboard import Controller

user32 = ctypes.WinDLL("user32", use_last_error=True)


class WindowFinder:
    def __init__(self) -> None:
        self._titles: list[tuple[int, str]] = []

    def find_by_substring(self, needle: str) -> int | None:
        self._titles.clear()
        lowered = needle.lower()

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def enum_proc(hwnd: int, _lparam: int) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True

            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True

            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, len(buffer))
            title = buffer.value.strip()
            if title:
                self._titles.append((hwnd, title))
            return True

        user32.EnumWindows(enum_proc, 0)

        for hwnd, title in self._titles:
            if lowered in title.lower():
                return hwnd
        return None

    @staticmethod
    def focus(hwnd: int) -> bool:
        user32.ShowWindow(hwnd, 5)
        return bool(user32.SetForegroundWindow(hwnd))

    @staticmethod
    def current_foreground() -> int | None:
        hwnd = user32.GetForegroundWindow()
        return hwnd or None


class AutoPressApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Auto Key Presser")
        self.root.geometry("420x280")
        self.root.resizable(False, False)

        self.running = False
        self.worker: threading.Thread | None = None
        self.controller = Controller()
        self.window_finder = WindowFinder()

        self.key_var = tk.StringVar(value="x")
        self.interval_var = tk.StringVar(value="2")
        self.target_title_var = tk.StringVar(value="")
        self.focus_delay_var = tk.StringVar(value="0.05")
        self.status_var = tk.StringVar(value="Status: Stopped")

        self._build_ui()
        keyboard.add_hotkey("F8", self.toggle_running)

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

        tk.Label(frame, text="Target window title contains:").grid(
            row=2, column=0, sticky="w", pady=(10, 0)
        )
        tk.Entry(frame, textvariable=self.target_title_var, width=24).grid(
            row=2, column=1, sticky="w", padx=8, pady=(10, 0)
        )

        tk.Label(frame, text="Focus delay (seconds):").grid(
            row=3, column=0, sticky="w", pady=(10, 0)
        )
        tk.Entry(frame, textvariable=self.focus_delay_var, width=12).grid(
            row=3, column=1, sticky="w", padx=8, pady=(10, 0)
        )

        btn_row = tk.Frame(frame)
        btn_row.grid(row=4, column=0, columnspan=2, pady=16, sticky="w")
        tk.Button(btn_row, text="Start", width=10, command=self.start).pack(side="left")
        tk.Button(btn_row, text="Stop", width=10, command=self.stop).pack(
            side="left", padx=(8, 0)
        )

        tk.Label(frame, textvariable=self.status_var).grid(
            row=5, column=0, columnspan=2, sticky="w"
        )
        tk.Label(frame, text="Global stop hotkey: F8").grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )
        tk.Label(frame, text="Matches the first visible window with that title.").grid(
            row=7, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )

    def start(self) -> None:
        if self.running:
            return

        key = self.key_var.get().strip()
        target_title = self.target_title_var.get().strip()
        if not key:
            messagebox.showerror("Invalid key", "Please provide a key (example: x).")
            return
        if not target_title:
            messagebox.showerror(
                "Invalid target",
                "Please provide part of the target window title.",
            )
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

        try:
            focus_delay = float(self.focus_delay_var.get().strip())
            if focus_delay < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid focus delay",
                "Focus delay must be a number greater than or equal to 0.",
            )
            return

        self.running = True
        self.status_var.set(
            f"Status: Running ({key} -> '{target_title}' every {interval}s)"
        )
        self.worker = threading.Thread(
            target=self._run_presser,
            args=(key, interval, target_title, focus_delay),
            daemon=True,
        )
        self.worker.start()

    def stop(self) -> None:
        self.running = False
        self.status_var.set("Status: Stopped")

    def toggle_running(self) -> None:
        if self.running:
            self.stop()
            return
        self.start()

    def _run_presser(
        self, key: str, interval: float, target_title: str, focus_delay: float
    ) -> None:
        normalized = key.strip().lower()
        if len(normalized) != 1:
            self.root.after(
                0,
                lambda: messagebox.showerror("Invalid key", f"Unsupported key: {key}"),
            )
            self.stop()
            return

        while self.running:
            current_window = self.window_finder.current_foreground()
            target_window = self.window_finder.find_by_substring(target_title)
            if target_window is None:
                self.root.after(
                    0,
                    lambda: self.status_var.set(
                        f"Status: Target not found ('{target_title}')"
                    ),
                )
                time.sleep(interval)
                continue

            if not self.window_finder.focus(target_window):
                self.root.after(
                    0,
                    lambda: self.status_var.set(
                        f"Status: Could not focus target ('{target_title}')"
                    ),
                )
                time.sleep(interval)
                continue

            time.sleep(focus_delay)
            self.controller.press(normalized)
            self.controller.release(normalized)

            if current_window and current_window != target_window:
                time.sleep(focus_delay)
                self.window_finder.focus(current_window)

            time.sleep(interval)


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
