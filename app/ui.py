"""UI Components and Windows GUI Management"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Optional, Callable, List
from datetime import datetime
from app.config import JobStatus, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE
from app.logger import JangiraLogger

class PrintJobUI:
    """Main UI window for Jangira AutoPrint"""
    
    def __init__(self, root: tk.Tk, job_callback: Optional[Callable] = None):
        self.root = root
        self.job_callback = job_callback
        self.logger = JangiraLogger.get_logger()
        self.selected_file: Optional[str] = None
        self.selected_printer: Optional[str] = None
        self.current_page_spec: str = ""
        
        self._setup_window()
        self._create_widgets()
    
    def _setup_window(self):
        """Setup main window"""
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(True, True)
        
        # Set minimum window size
        self.root.minsize(800, 600)
    
    def _create_widgets(self):
        """Create UI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Jangira AutoPrint",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="1. Select PDF File", padding=10)
        file_frame.pack(fill=tk.X, pady=10)
        
        self.file_label = ttk.Label(file_frame, text="No file selected", foreground="gray")
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            file_frame,
            text="Browse...",
            command=self._browse_file
        ).pack(side=tk.RIGHT, padx=5)
        
        # Printer selection frame
        printer_frame = ttk.LabelFrame(main_frame, text="2. Select Printer", padding=10)
        printer_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(printer_frame, text="Printer:").pack(side=tk.LEFT, padx=5)
        
        self.printer_var = tk.StringVar()
        self.printer_combo = ttk.Combobox(
            printer_frame,
            textvariable=self.printer_var,
            state="readonly",
            width=40
        )
        self.printer_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.printer_combo.bind("<<ComboboxSelected>>", self._on_printer_changed)
        
        ttk.Button(
            printer_frame,
            text="Refresh",
            command=self._refresh_printers
        ).pack(side=tk.RIGHT, padx=5)
        
        # Print options frame
        options_frame = ttk.LabelFrame(main_frame, text="3. Print Options", padding=10)
        options_frame.pack(fill=tk.X, pady=10)
        
        # Page specification
        page_frame = ttk.Frame(options_frame)
        page_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(page_frame, text="Pages (e.g., 1-5, 7, 10):").pack(side=tk.LEFT, padx=5)
        
        self.pages_var = tk.StringVar(value="All")
        self.pages_entry = ttk.Entry(page_frame, textvariable=self.pages_var, width=30)
        self.pages_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Copies
        copies_frame = ttk.Frame(options_frame)
        copies_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(copies_frame, text="Copies:").pack(side=tk.LEFT, padx=5)
        
        self.copies_var = tk.StringVar(value="1")
        self.copies_spin = ttk.Spinbox(
            copies_frame,
            from_=1,
            to=999,
            textvariable=self.copies_var,
            width=10
        )
        self.copies_spin.pack(side=tk.LEFT, padx=5)
        
        # Print button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        self.print_button = ttk.Button(
            button_frame,
            text="Print",
            command=self._submit_print,
            state="disabled"
        )
        self.print_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(
            button_frame,
            text="Clear",
            command=self._clear_form
        ).pack(side=tk.LEFT, padx=5)
        
        # Job history frame
        history_frame = ttk.LabelFrame(main_frame, text="Recent Jobs", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create treeview for job history
        columns = ("ID", "File", "Status", "Time")
        self.jobs_tree = ttk.Treeview(
            history_frame,
            columns=columns,
            height=10,
            show="headings"
        )
        
        for col in columns:
            self.jobs_tree.column(col, width=100)
            self.jobs_tree.heading(col, text=col)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            history_frame,
            orient=tk.VERTICAL,
            command=self.jobs_tree.yview
        )
        self.jobs_tree.configure(yscroll=scrollbar.set)
        
        self.jobs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=2, pady=2)
    
    def _browse_file(self):
        """Browse for PDF file"""
        filename = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            self.selected_file = filename
            file_name = Path(filename).name
            self.file_label.config(
                text=f"Selected: {file_name}",
                foreground="black"
            )
            self._update_print_button_state()
    
    def _refresh_printers(self):
        """Refresh printer list"""
        if self.job_callback:
            printers = self.job_callback({
                "action": "get_printers"
            })
            if printers:
                self.printer_combo['values'] = printers
                if printers:
                    self.printer_combo.current(0)
                    self.selected_printer = printers[0]
                    self._update_print_button_state()
    
    def _on_printer_changed(self, event):
        """Handle printer selection change"""
        self.selected_printer = self.printer_var.get()
    
    def _submit_print(self):
        """Submit print job"""
        if not self.selected_file or not self.selected_printer:
            messagebox.showerror("Error", "Please select a file and printer")
            return
        
        try:
            copies = int(self.copies_var.get())
            if copies < 1:
                raise ValueError("Copies must be at least 1")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid copies value: {e}")
            return
        
        page_spec = self.pages_var.get()
        if page_spec.lower() == "all":
            page_spec = ""
        
        self.current_page_spec = page_spec
        
        # Submit job via callback
        if self.job_callback:
            result = self.job_callback({
                "action": "submit_job",
                "file_path": self.selected_file,
                "page_spec": page_spec,
                "copies": copies,
                "printer_name": self.selected_printer
            })
            
            if result.get("success"):
                messagebox.showinfo("Success", f"Job submitted: {result.get('job_id')}")
                self._clear_form()
                self._refresh_job_history()
            else:
                messagebox.showerror("Error", result.get("error", "Unknown error"))
    
    def _clear_form(self):
        """Clear the form"""
        self.selected_file = None
        self.file_label.config(text="No file selected", foreground="gray")
        self.pages_var.set("All")
        self.copies_var.set("1")
        self._update_print_button_state()
    
    def _update_print_button_state(self):
        """Update print button state"""
        if self.selected_file and self.selected_printer:
            self.print_button.config(state="normal")
        else:
            self.print_button.config(state="disabled")
    
    def _refresh_job_history(self):
        """Refresh job history display"""
        # Clear current items
        for item in self.jobs_tree.get_children():
            self.jobs_tree.delete(item)
        
        # Get recent jobs via callback
        if self.job_callback:
            jobs = self.job_callback({
                "action": "get_history",
                "limit": 10
            })
            
            for job in jobs:
                self.jobs_tree.insert(
                    "",
                    0,
                    values=(
                        job.get("id", "")[:12],
                        Path(job.get("file_path", "")).name,
                        job.get("status", ""),
                        job.get("created_at", "")
                    )
                )
    
    def update_status(self, message: str):
        """Update status bar"""
        self.status_var.set(message)
        self.root.update()
    
    def show_error(self, title: str, message: str):
        """Show error dialog"""
        messagebox.showerror(title, message)
    
    def show_info(self, title: str, message: str):
        """Show info dialog"""
        messagebox.showinfo(title, message)
    
    def update_job_status(self, job_id: str, status: str):
        """Update displayed job status"""
        self.update_status(f"Job {job_id[:12]}: {status}")
        self._refresh_job_history()

class SettingsDialog:
    """Settings dialog window"""
    
    def __init__(self, parent: tk.Tk, settings: dict, callback: Optional[Callable] = None):
        self.parent = parent
        self.settings = settings
        self.callback = callback
        self.result = {}
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create settings widgets"""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Default printer
        ttk.Label(main_frame, text="Default Printer:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.printer_var = tk.StringVar(value=self.settings.get("default_printer", ""))
        ttk.Entry(main_frame, textvariable=self.printer_var, width=40).grid(
            row=0, column=1, sticky=tk.EW, pady=5
        )
        
        # Log level
        ttk.Label(main_frame, text="Log Level:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.log_level_var = tk.StringVar(value=self.settings.get("log_level", "INFO"))
        ttk.Combobox(
            main_frame,
            textvariable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            state="readonly"
        ).grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        # Auto print
        self.auto_print_var = tk.BooleanVar(value=self.settings.get("auto_print", False))
        ttk.Checkbutton(
            main_frame,
            text="Auto-print pending jobs on startup",
            variable=self.auto_print_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=20)
        
        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.LEFT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)
    
    def _save(self):
        """Save settings"""
        self.result = {
            "default_printer": self.printer_var.get(),
            "log_level": self.log_level_var.get(),
            "auto_print": self.auto_print_var.get()
        }
        
        if self.callback:
            self.callback(self.result)
        
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancel dialog"""
        self.dialog.destroy()
