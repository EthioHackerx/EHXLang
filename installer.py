"""
EHXLang v1.0.0 Windows Setup Wizard
Developed by Yonatan Muluken ( ETHIO HACKER X )

Multi-Step Standard Windows Setup Wizard:
Step 1: Admin / User Mode Privileges
Step 2: Welcome & License Agreement (Accept / Decline)
Step 3: Installation Directory Selection
Step 4: Installation Components / Options
Step 5: File Deployment with Progress Animation
Step 6: Completion Confirmation
"""

import os
import sys
import shutil
import winreg
import ctypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time

APP_NAME = "EHXLang"
APP_VERSION = "1.0.0"
AUTHOR = "Yonatan Muluken ( ETHIO HACKER X )"
DEFAULT_USER_DIR = os.path.join(os.environ.get("LOCALAPPDATA", "C:\\"), "Programs", "EHXLang")
DEFAULT_SYSTEM_DIR = os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "EHXLang")


def is_user_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


class EHXWizardApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} {APP_VERSION} Setup Wizard")
        self.root.geometry("560x420")
        self.root.resizable(False, False)

        self.style = ttk.Style()
        try:
            self.style.theme_use("vista")
        except Exception:
            pass

        # Wizard State
        self.current_step = 0
        self.is_admin = is_user_admin()
        default_dir = DEFAULT_SYSTEM_DIR if self.is_admin else DEFAULT_USER_DIR

        self.install_dir = tk.StringVar(value=default_dir)
        self.license_agreed = tk.BooleanVar(value=False)
        self.add_to_path = tk.BooleanVar(value=True)
        self.install_vscode_ext = tk.BooleanVar(value=True)
        self.install_examples = tk.BooleanVar(value=True)
        self.install_pdf_guide = tk.BooleanVar(value=True)

        # Main frame containers
        self.header_frame = tk.Frame(self.root, bg="#ffffff", height=70)
        self.header_frame.pack(fill=tk.X, side=tk.TOP)
        self.header_frame.pack_propagate(False)

        self.header_title = tk.Label(
            self.header_frame,
            text="",
            font=("Segoe UI", 11, "bold"),
            bg="#ffffff",
            fg="#000000",
            anchor="w"
        )
        self.header_title.pack(fill=tk.X, padx=20, pady=(12, 2))

        self.header_subtitle = tk.Label(
            self.header_frame,
            text="",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#555555",
            anchor="w"
        )
        self.header_subtitle.pack(fill=tk.X, padx=30, pady=(0, 10))

        ttk.Separator(self.root, orient="horizontal").pack(fill=tk.X)

        # Content area
        self.content_frame = tk.Frame(self.root, bg="#f5f6f8", padx=25, pady=15)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Separator(self.root, orient="horizontal").pack(fill=tk.X)

        # Bottom navigation bar
        self.bottom_frame = tk.Frame(self.root, bg="#eceef1", height=50)
        self.bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.bottom_frame.pack_propagate(False)

        self.brand_lbl = tk.Label(
            self.bottom_frame,
            text=f"{APP_NAME} v{APP_VERSION} Setup",
            font=("Segoe UI", 8),
            bg="#eceef1",
            fg="#888888"
        )
        self.brand_lbl.pack(side=tk.LEFT, padx=15)

        self.cancel_btn = ttk.Button(self.bottom_frame, text="Cancel", command=self.on_cancel)
        self.cancel_btn.pack(side=tk.RIGHT, padx=(5, 15), pady=12)

        self.next_btn = ttk.Button(self.bottom_frame, text="Next >", command=self.go_next)
        self.next_btn.pack(side=tk.RIGHT, padx=5, pady=12)

        self.back_btn = ttk.Button(self.bottom_frame, text="< Back", command=self.go_back)
        self.back_btn.pack(side=tk.RIGHT, padx=5, pady=12)

        self.render_step()

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def render_step(self):
        self.clear_content()

        # Step 0: Welcome & Privilege Notice
        if self.current_step == 0:
            self.header_title.config(text=f"Welcome to the {APP_NAME} Setup Wizard")
            self.header_subtitle.config(text=f"Setup will install {APP_NAME} v{APP_VERSION} on your system.")
            self.back_btn.config(state="disabled")
            self.next_btn.config(state="normal", text="Next >")

            welcome_lbl = tk.Label(
                self.content_frame,
                text=f"{APP_NAME} is a modern, human-readable programming language\ndeveloped by {AUTHOR}.\n\n"
                     "This wizard will guide you through the installation process.",
                font=("Segoe UI", 9),
                bg="#f5f6f8",
                justify="left"
            )
            welcome_lbl.pack(anchor="w", pady=(5, 15))

            # Privilege box
            priv_bg = "#e0f2fe" if self.is_admin else "#fef3c7"
            priv_fg = "#0369a1" if self.is_admin else "#92400e"
            priv_title = "Administrator Mode Active" if self.is_admin else "Standard User Mode"
            priv_msg = (
                "You have administrative privileges. EHXLang can be installed system-wide."
                if self.is_admin else
                "Running in normal user mode. EHXLang will install to your personal local profile.\n"
                "(To install for all users, right-click the setup and select 'Run as administrator')."
            )

            box = tk.Frame(self.content_frame, bg=priv_bg, bd=1, relief="solid")
            box.pack(fill=tk.X, pady=10)
            tk.Label(box, text=f"• {priv_title}", font=("Segoe UI", 9, "bold"), bg=priv_bg, fg=priv_fg).pack(anchor="w", padx=12, pady=(8, 2))
            tk.Label(box, text=priv_msg, font=("Segoe UI", 8), bg=priv_bg, fg="#333333", justify="left").pack(anchor="w", padx=12, pady=(0, 8))

        # Step 1: License Agreement
        elif self.current_step == 1:
            self.header_title.config(text="License Agreement")
            self.header_subtitle.config(text="Please review the license terms before proceeding.")
            self.back_btn.config(state="normal")
            self.next_btn.config(text="Next >")
            self.update_license_next_state()

            license_text = (
                f"{APP_NAME} - End User Agreement\n"
                f"Copyright (c) 2026 {AUTHOR}.\n\n"
                "Permission is hereby granted, free of charge, to any person obtaining a copy "
                "of this software and associated documentation files, to deal in the Software "
                "without restriction, including without limitation the rights to use, copy, "
                "modify, merge, publish, distribute, and permit persons to whom the Software is "
                "furnished to do so.\n\n"
                "THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR "
                "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, "
                "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT."
            )

            txt = tk.Text(self.content_frame, height=8, font=("Consolas", 8), wrap="word")
            txt.insert("1.0", license_text)
            txt.config(state="disabled")
            txt.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            rb_agree = ttk.Radiobutton(
                self.content_frame,
                text="I accept the agreement",
                variable=self.license_agreed,
                value=True,
                command=self.update_license_next_state
            )
            rb_agree.pack(anchor="w", pady=2)

            rb_disagree = ttk.Radiobutton(
                self.content_frame,
                text="I do not accept the agreement",
                variable=self.license_agreed,
                value=False,
                command=self.update_license_next_state
            )
            rb_disagree.pack(anchor="w", pady=2)

        # Step 2: Destination Folder Selection
        elif self.current_step == 2:
            self.header_title.config(text="Select Destination Location")
            self.header_subtitle.config(text=f"Where should {APP_NAME} be installed?")
            self.back_btn.config(state="normal")
            self.next_btn.config(state="normal", text="Next >")

            tk.Label(
                self.content_frame,
                text=f"Setup will install {APP_NAME} into the following folder.\n"
                     "To continue, click Next. If you would like to select a different folder, click Browse.",
                font=("Segoe UI", 9),
                bg="#f5f6f8",
                justify="left"
            ).pack(anchor="w", pady=(0, 15))

            dest_box = tk.LabelFrame(self.content_frame, text="Destination Folder", font=("Segoe UI", 9, "bold"), bg="#f5f6f8", padx=10, pady=10)
            dest_box.pack(fill=tk.X)

            entry = ttk.Entry(dest_box, textvariable=self.install_dir, font=("Segoe UI", 9))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

            browse_btn = ttk.Button(dest_box, text="Browse...", command=self.browse_folder)
            browse_btn.pack(side=tk.RIGHT)

            tk.Label(
                self.content_frame,
                text="At least 15 MB of free disk space is required.",
                font=("Segoe UI", 8),
                bg="#f5f6f8",
                fg="#666666"
            ).pack(anchor="w", pady=(15, 0))

        # Step 3: Components & Environment Configuration
        elif self.current_step == 3:
            self.header_title.config(text="Select Additional Tasks")
            self.header_subtitle.config(text="Which additional tasks should be performed?")
            self.back_btn.config(state="normal")
            self.next_btn.config(state="normal", text="Install")

            tk.Label(
                self.content_frame,
                text="Select the additional tasks you would like Setup to perform:",
                font=("Segoe UI", 9),
                bg="#f5f6f8"
            ).pack(anchor="w", pady=(0, 10))

            ttk.Checkbutton(
                self.content_frame,
                text="Add 'ehx' command to system PATH (Run directly from terminal / PowerShell)",
                variable=self.add_to_path
            ).pack(anchor="w", pady=4)

            ttk.Checkbutton(
                self.content_frame,
                text="Install official VS Code Extension (Syntax highlighting & indentation)",
                variable=self.install_vscode_ext
            ).pack(anchor="w", pady=4)

            ttk.Checkbutton(
                self.content_frame,
                text="Include standard examples & cybersecurity automation scripts",
                variable=self.install_examples
            ).pack(anchor="w", pady=4)

            ttk.Checkbutton(
                self.content_frame,
                text="Include official PDF Reference Manual (EHXLang_Official_Guide.pdf)",
                variable=self.install_pdf_guide
            ).pack(anchor="w", pady=4)

        # Step 4: Installation Progress & Animation
        elif self.current_step == 4:
            self.header_title.config(text="Installing")
            self.header_subtitle.config(text=f"Please wait while Setup installs {APP_NAME} on your computer.")
            self.back_btn.config(state="disabled")
            self.next_btn.config(state="disabled")
            self.cancel_btn.config(state="disabled")

            self.status_lbl = tk.Label(
                self.content_frame,
                text="Extracting files and configuring environment...",
                font=("Segoe UI", 9),
                bg="#f5f6f8"
            )
            self.status_lbl.pack(anchor="w", pady=(15, 10))

            self.progress_bar = ttk.Progressbar(self.content_frame, orient="horizontal", mode="determinate")
            self.progress_bar.pack(fill=tk.X, pady=10)

            threading.Thread(target=self.run_installation_worker, daemon=True).start()

        # Step 5: Finished
        elif self.current_step == 5:
            self.header_title.config(text="Installation Complete")
            self.header_subtitle.config(text=f"{APP_NAME} has been successfully installed on your computer.")
            self.back_btn.config(state="disabled")
            self.cancel_btn.config(state="disabled")
            self.next_btn.config(state="normal", text="Finish", command=self.root.destroy)

            finish_msg = (
                f"Successfully installed {APP_NAME} v{APP_VERSION}!\n\n"
                f"Location:\n{self.install_dir.get()}\n\n"
                "Configured Components:\n"
                "✓ 'ehx' command line launcher (Terminal & PowerShell)\n"
                "✓ Official VS Code syntax highlighter & indentation\n"
                "✓ Full Standard Library & Automation Runtime\n\n"
                "You can now run 'ehx --version' or 'ehx' in any new terminal window."
            )
            tk.Label(
                self.content_frame,
                text=finish_msg,
                font=("Segoe UI", 9),
                bg="#f5f6f8",
                justify="left"
            ).pack(anchor="w", pady=10)

    def update_license_next_state(self):
        if self.current_step == 1:
            if self.license_agreed.get():
                self.next_btn.config(state="normal")
            else:
                self.next_btn.config(state="disabled")

    def browse_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.install_dir.get(), title="Select Install Directory")
        if chosen:
            self.install_dir.set(os.path.normpath(chosen))

    def go_next(self):
        if self.current_step < 4:
            self.current_step += 1
            self.render_step()

    def go_back(self):
        if self.current_step > 0 and self.current_step != 4:
            self.current_step -= 1
            self.render_step()

    def on_cancel(self):
        if messagebox.askyesno("Exit Setup", f"Are you sure you want to exit {APP_NAME} Setup?"):
            self.root.destroy()

    def run_installation_worker(self):
        target_dir = self.install_dir.get().strip()
        base_dir = os.path.dirname(os.path.abspath(__file__))

        try:
            # Stage 1: Directory Setup
            self.update_progress(10, "Creating installation directory...")
            os.makedirs(target_dir, exist_ok=True)
            time.sleep(0.2)

            # Stage 2: Core Files
            self.update_progress(30, "Copying core language runtime...")
            core_files = ["ehx.py", "lexer.py", "parser.py", "tokens.py", "interpreter.py"]
            for cf in core_files:
                src = os.path.join(base_dir, cf)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(target_dir, cf))
            time.sleep(0.2)

            # Stage 3: Batch Launchers
            self.update_progress(50, "Generating CLI launchers...")
            bat_path = os.path.join(target_dir, "ehx.bat")
            with open(bat_path, "w", encoding="utf-8") as bf:
                bf.write(f'@echo off\npython "%~dp0ehx.py" %*\n')

            cmd_path = os.path.join(target_dir, "ehx.cmd")
            with open(cmd_path, "w", encoding="utf-8") as cf:
                cf.write(f'@echo off\npython "%~dp0ehx.py" %*\n')
            time.sleep(0.2)

            # Stage 4: Examples & Documentation
            if self.install_examples.get():
                self.update_progress(65, "Deploying standard library examples...")
                src_examples = os.path.join(base_dir, "examples")
                if os.path.exists(src_examples):
                    dst_examples = os.path.join(target_dir, "examples")
                    shutil.copytree(src_examples, dst_examples, dirs_exist_ok=True)

            if self.install_pdf_guide.get():
                self.update_progress(75, "Copying official documentation and manual...")
                for doc in ["EHXLang_Complete_Programming_Book.pdf", "README.md"]:
                    s = os.path.join(base_dir, doc)
                    if os.path.exists(s):
                        shutil.copy2(s, os.path.join(target_dir, doc))

            # Stage 5: VS Code Extension
            if self.install_vscode_ext.get():
                self.update_progress(85, "Installing VS Code Extension...")
                user_home = os.path.expanduser("~")
                vscode_ext_dir = os.path.join(user_home, ".vscode", "extensions", "ehx-vscode")
                src_ext_dir = os.path.join(base_dir, "ehx-vscode")
                if os.path.exists(src_ext_dir):
                    os.makedirs(vscode_ext_dir, exist_ok=True)
                    for item in os.listdir(src_ext_dir):
                        s = os.path.join(src_ext_dir, item)
                        d = os.path.join(vscode_ext_dir, item)
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy2(s, d)

            # Stage 6: PATH Registration
            if self.add_to_path.get():
                self.update_progress(95, "Configuring system PATH...")
                self.register_path(target_dir)

            self.update_progress(100, "Finalizing installation...")
            time.sleep(0.3)

            # Move to finished step
            self.root.after(0, self.finish_success)

        except Exception as e:
            self.root.after(0, self.finish_error, str(e))

    def update_progress(self, val, msg):
        self.root.after(0, lambda: self._apply_progress(val, msg))

    def _apply_progress(self, val, msg):
        self.progress_bar["value"] = val
        self.status_lbl.config(text=msg)

    def register_path(self, target_dir):
        # Choose system path if admin, user path if normal
        root_key = winreg.HKEY_LOCAL_MACHINE if self.is_admin else winreg.HKEY_CURRENT_USER
        subkey = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment" if self.is_admin else r"Environment"

        try:
            with winreg.OpenKey(root_key, subkey, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                try:
                    current_path, _ = winreg.QueryValueEx(key, "Path")
                except FileNotFoundError:
                    current_path = ""

                paths = [p.strip() for p in current_path.split(";") if p.strip()]
                normalized = os.path.normpath(target_dir).lower()
                if not any(os.path.normpath(p).lower() == normalized for p in paths):
                    paths.append(target_dir)
                    winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, ";".join(paths))

            # Broadcast WM_SETTINGCHANGE
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            SMTO_ABORTIFHUNG = 0x0002
            result = ctypes.c_ulong()
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
                SMTO_ABORTIFHUNG, 5000, ctypes.byref(result)
            )
        except Exception:
            pass

    def finish_success(self):
        self.current_step = 5
        self.render_step()

    def finish_error(self, err_msg):
        messagebox.showerror("Installation Error", f"Installation failed with error:\n\n{err_msg}")
        self.root.destroy()


def main():
    root = tk.Tk()
    app = EHXWizardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
