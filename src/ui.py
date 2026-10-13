"""Tkinter UI. Long-running model/audio operations run outside the UI thread."""
from __future__ import annotations
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from .history import list_transcripts, read_transcript, save_transcript
from .recorder import AudioRecorder
from .settings import DEFAULT_OUTPUT_DIR, load_settings, save_settings
from .theme import PALETTES
from .transcriber import PersianTranscriber


class PersianSTTApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Persian STT — گفتار به متن")
        self.geometry("1050x680")
        self.minsize(820, 560)
        self.settings = load_settings()
        self.palette = PALETTES[self.settings["theme"]]
        self.output_dir = Path(self.settings["output_dir"])
        self.recorder = AudioRecorder()
        self.transcriber = PersianTranscriber()
        self.events: queue.Queue = queue.Queue()
        self.record_started = 0.0
        self.record_timer_job = None
        self.current_file: Path | None = None
        self.busy = False
        self._build_ui()
        self.apply_theme()
        self.refresh_history()
        self.after(100, self._poll_events)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        self.configure(padx=16, pady=12)
        header = tk.Frame(self, bd=0)
        header.pack(fill="x", pady=(0, 12))
        tk.Label(header, text="گفتار به متن فارسی", font=("Segoe UI", 20, "bold")).pack(side="left")
        self.settings_button = tk.Button(header, text="⚙ Settings", command=self.open_settings, relief="flat", padx=12, pady=7)
        self.settings_button.pack(side="right")

        body = tk.Frame(self)
        body.pack(fill="both", expand=True)
        self.history_panel = tk.Frame(body, width=250, padx=10, pady=10)
        self.history_panel.pack(side="left", fill="y", padx=(0, 12))
        self.history_panel.pack_propagate(False)
        tk.Label(self.history_panel, text="Transcript history", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.folder_label = tk.Label(self.history_panel, text="", anchor="w", justify="left", wraplength=220)
        self.folder_label.pack(fill="x", pady=(6, 8))
        self.history_list = tk.Listbox(self.history_panel, activestyle="dotbox", exportselection=False, borderwidth=0, highlightthickness=1)
        self.history_list.pack(fill="both", expand=True)
        self.history_list.bind("<<ListboxSelect>>", self._select_history)
        history_actions = tk.Frame(self.history_panel)
        history_actions.pack(fill="x", pady=(8, 0))
        self.open_folder_button = tk.Button(history_actions, text="Open folder", command=self.open_output_folder, relief="flat")
        self.open_folder_button.pack(side="left", fill="x", expand=True)
        self.delete_button = tk.Button(history_actions, text="Delete", command=self.delete_selected, relief="flat")
        self.delete_button.pack(side="left", fill="x", expand=True, padx=(6, 0))

        self.main_panel = tk.Frame(body, padx=14, pady=12)
        self.main_panel.pack(side="left", fill="both", expand=True)
        self.status_label = tk.Label(self.main_panel, text="Ready — press Start recording", anchor="w")
        self.status_label.pack(fill="x", pady=(0, 8))
        controls = tk.Frame(self.main_panel)
        controls.pack(fill="x", pady=(0, 10))
        self.record_button = tk.Button(controls, text="● Start recording", command=self.toggle_recording, relief="flat", padx=16, pady=10)
        self.record_button.pack(side="left")
        self.duration_label = tk.Label(controls, text="00:00", font=("Consolas", 12, "bold"))
        self.duration_label.pack(side="left", padx=12)
        self.copy_button = tk.Button(controls, text="Copy text", command=self.copy_text, relief="flat", padx=10, pady=8)
        self.copy_button.pack(side="right")
        self.save_button = tk.Button(controls, text="Save as…", command=self.save_as, relief="flat", padx=10, pady=8)
        self.save_button.pack(side="right", padx=(0, 6))
        self.transcript = tk.Text(self.main_panel, wrap="word", undo=True, padx=12, pady=12, borderwidth=0, highlightthickness=1, font=("Segoe UI", 13))
        self.transcript.pack(fill="both", expand=True)
        self.transcript.tag_configure("rtl", justify="right")
        self.transcript.bind("<KeyRelease>", self._align_text)
        self.bind_all("<Return>", self._enter_shortcut, add="+")
        self.footer = tk.Frame(self.main_panel)
        self.footer.pack(fill="x", pady=(10, 0))
        self.theme_button = tk.Button(self.footer, text="Switch to light theme", command=self.toggle_theme, relief="flat", padx=10, pady=7)
        self.theme_button.pack(side="left")
        self.auto_save_label = tk.Label(self.footer, text="Auto-save: on")
        self.auto_save_label.pack(side="right")

    def apply_theme(self):
        p = self.palette
        self.configure(bg=p["bg"])
        def walk(widget):
            for child in widget.winfo_children():
                if isinstance(child, tk.Text):
                    child.configure(bg=p["input"], fg=p["text"], insertbackground=p["text"], selectbackground=p["accent"], highlightbackground=p["border"], highlightcolor=p["accent"])
                elif isinstance(child, tk.Listbox):
                    child.configure(bg=p["input"], fg=p["text"], selectbackground=p["accent"], selectforeground="#ffffff", highlightbackground=p["border"])
                elif isinstance(child, tk.Button):
                    child.configure(bg=p["panel"], fg=p["text"], activebackground=p["accent"], activeforeground="#ffffff", relief="flat", highlightthickness=0)
                elif isinstance(child, (tk.Frame, tk.Label, tk.Checkbutton, tk.Radiobutton)):
                    try:
                        child.configure(bg=p["bg"], fg=p["text"])
                    except tk.TclError:
                        pass
                walk(child)
        walk(self)
        for panel in (self.history_panel, self.main_panel):
            panel.configure(bg=p["panel"])
        self.theme_button.configure(text="Switch to light theme" if self.settings["theme"] == "dark" else "Switch to dark theme")
        self.auto_save_label.configure(text=f"Auto-save: {'on' if self.settings['auto_save'] else 'off'}")
        self.folder_label.configure(fg=p["muted"])
        self.status_label.configure(fg=p["muted"])
        self.duration_label.configure(fg=p["accent"])

    def _persist(self):
        self.settings["output_dir"] = str(self.output_dir)
        save_settings(self.settings)

    def toggle_theme(self):
        self.settings["theme"] = "light" if self.settings["theme"] == "dark" else "dark"
        self.palette = PALETTES[self.settings["theme"]]
        self._persist()
        self.apply_theme()

    def toggle_recording(self):
        if self.busy:
            return
        if not self.recorder.recording:
            try:
                self.recorder.start()
            except Exception as exc:
                messagebox.showerror("Microphone error", f"Could not start recording. Check Windows microphone permissions and the selected input device.\n\n{exc}", parent=self)
                return
            self.record_started = time.monotonic()
            self.record_button.configure(text="■ Stop recording")
            self.status_label.configure(text="Recording… press Enter or Stop to finish")
            self._tick_duration()
        else:
            self._stop_recording()

    def _tick_duration(self):
        if not self.recorder.recording:
            return
        seconds = int(time.monotonic() - self.record_started)
        self.duration_label.configure(text=f"{seconds // 60:02d}:{seconds % 60:02d}")
        self.record_timer_job = self.after(250, self._tick_duration)

    def _stop_recording(self):
        try:
            with tempfile.NamedTemporaryFile(prefix="persian_stt_", suffix=".wav", delete=False) as handle:
                audio_path = Path(handle.name)
            audio_path.unlink(missing_ok=True)
            self.recorder.stop(audio_path)
        except Exception as exc:
            messagebox.showerror("Recording error", str(exc), parent=self)
            self.record_button.configure(text="● Start recording")
            self.status_label.configure(text="Recording failed")
            return
        self.record_button.configure(text="● Start recording")
        self.status_label.configure(text="Transcribing locally on CPU…")
        self.busy = True
        threading.Thread(target=self._transcribe_worker, args=(audio_path,), daemon=True).start()

    def _transcribe_worker(self, audio_path: Path):
        try:
            result = self.transcriber.transcribe(audio_path)
            saved = None
            if result and self.settings.get("auto_save", True):
                saved = save_transcript(self.output_dir, result)
            self.events.put(("success", result, saved))
        except Exception as exc:
            self.events.put(("error", str(exc)))
        finally:
            audio_path.unlink(missing_ok=True)

    def _poll_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "success":
                    _, result, saved = event
                    self.transcript.delete("1.0", "end")
                    self.transcript.insert("1.0", result)
                    self.transcript.tag_add("rtl", "1.0", "end")
                    self.current_file = saved
                    self.status_label.configure(text=(f"Transcription complete · saved to {saved.name}" if saved else "Transcription complete · not auto-saved"))
                    self.refresh_history()
                else:
                    self.status_label.configure(text="Transcription failed")
                    messagebox.showerror("Transcription error", event[1], parent=self)
                self.busy = False
        except queue.Empty:
            pass
        self.after(100, self._poll_events)

    def _enter_shortcut(self, event=None):
        # Preserve Enter as a newline while the transcript editor has focus.
        if self.focus_get() == self.transcript:
            return
        if not self.busy:
            self.toggle_recording()
        return "break"

    def _align_text(self, _event=None):
        self.transcript.tag_add("rtl", "1.0", "end")

    def refresh_history(self):
        self.history_files = list_transcripts(self.output_dir)
        self.history_list.delete(0, "end")
        for path in self.history_files:
            self.history_list.insert("end", path.stem)
        self.folder_label.configure(text=str(self.output_dir))

    def _select_history(self, _event=None):
        selection = self.history_list.curselection()
        if not selection:
            return
        path = self.history_files[selection[0]]
        try:
            self.transcript.delete("1.0", "end")
            self.transcript.insert("1.0", read_transcript(path))
            self.transcript.tag_add("rtl", "1.0", "end")
            self.current_file = path
            self.status_label.configure(text=f"Loaded {path.name}")
        except OSError as exc:
            messagebox.showerror("Could not open transcript", str(exc), parent=self)

    def copy_text(self):
        text = self.transcript.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_label.configure(text="Transcript copied to clipboard")

    def save_as(self):
        text = self.transcript.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showinfo("Nothing to save", "Transcribe or enter some text first.", parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, title="Save transcript", initialdir=str(self.output_dir), initialfile="transcript.txt", defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if path:
            try:
                Path(path).write_text(text + "\n", encoding="utf-8")
                self.current_file = Path(path)
                self.status_label.configure(text=f"Saved {Path(path).name}")
                self.refresh_history()
            except OSError as exc:
                messagebox.showerror("Save failed", str(exc), parent=self)

    def open_output_folder(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                import os
                os.startfile(str(self.output_dir))
            else:
                subprocess.Popen(["xdg-open", str(self.output_dir)])
        except Exception as exc:
            messagebox.showerror("Could not open folder", str(exc), parent=self)

    def delete_selected(self):
        selection = self.history_list.curselection()
        if not selection:
            return
        path = self.history_files[selection[0]]
        if not messagebox.askyesno("Delete transcript", f"Permanently delete {path.name}?", parent=self):
            return
        try:
            path.unlink()
            if self.current_file == path:
                self.current_file = None
            self.refresh_history()
            self.status_label.configure(text=f"Deleted {path.name}")
        except OSError as exc:
            messagebox.showerror("Delete failed", str(exc), parent=self)

    def open_settings(self):
        win = tk.Toplevel(self)
        win.title("Settings")
        win.transient(self)
        win.grab_set()
        win.resizable(False, False)
        win.configure(bg=self.palette["bg"], padx=18, pady=18)
        tk.Label(win, text="Settings", font=("Segoe UI", 16, "bold"), bg=self.palette["bg"], fg=self.palette["text"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))
        folder_var = tk.StringVar(value=str(self.output_dir))
        auto_var = tk.BooleanVar(value=self.settings["auto_save"])
        tk.Label(win, text="Transcript folder", bg=self.palette["bg"], fg=self.palette["text"]).grid(row=1, column=0, sticky="w", pady=6)
        entry = tk.Entry(win, textvariable=folder_var, width=44)
        entry.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        tk.Button(win, text="Browse…", command=lambda: self._pick_folder(folder_var), bg=self.palette["panel"], fg=self.palette["text"]).grid(row=2, column=1, padx=(8, 0))
        tk.Checkbutton(win, text="Automatically save each completed transcript", variable=auto_var, bg=self.palette["bg"], fg=self.palette["text"], selectcolor=self.palette["panel"], activebackground=self.palette["bg"]).grid(row=3, column=0, columnspan=2, sticky="w", pady=8)
        tk.Label(win, text="Theme can be changed with the button at the bottom of the main window.", wraplength=390, justify="left", bg=self.palette["bg"], fg=self.palette["muted"]).grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 12))
        def save_and_close():
            chosen = Path(folder_var.get()).expanduser()
            if not folder_var.get().strip():
                messagebox.showerror("Invalid folder", "Choose a transcript folder.", parent=win)
                return
            try:
                chosen.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                messagebox.showerror("Folder error", str(exc), parent=win)
                return
            self.output_dir = chosen
            self.settings["auto_save"] = auto_var.get()
            self._persist()
            self.refresh_history()
            self.apply_theme()
            win.destroy()
        tk.Button(win, text="Save settings", command=save_and_close, bg=self.palette["accent"], fg="#ffffff", padx=14, pady=8).grid(row=5, column=0, sticky="w", pady=(8, 0))
        tk.Button(win, text="Cancel", command=win.destroy, bg=self.palette["panel"], fg=self.palette["text"], padx=14, pady=8).grid(row=5, column=1, sticky="e", pady=(8, 0))

    def _pick_folder(self, variable):
        chosen = filedialog.askdirectory(parent=self, initialdir=variable.get() or str(DEFAULT_OUTPUT_DIR), title="Choose transcript folder")
        if chosen:
            variable.set(chosen)

    def _on_close(self):
        if self.recorder.recording:
            if not messagebox.askyesno("Recording in progress", "Stop recording and close the application? The current recording will not be transcribed.", parent=self):
                return
            try:
                self.recorder._stream.abort()
                self.recorder._stream.close()
            except Exception:
                pass
        self._persist()
        self.destroy()
