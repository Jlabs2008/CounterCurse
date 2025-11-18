import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from pathlib import Path
import sys

# Import your ProfanityFilter class
from clean import ProfanityFilter


class CurseCleanerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Curse Cleaner")
        self.root.geometry("700x550")
        self.root.resizable(False, False)

        # Set color scheme
        self.bg_color = "#f0f0f0"
        self.accent_color = "#4a90e2"
        self.button_color = "#5cff67"
        self.button_hover = "#99ffa0"

        self.root.configure(bg=self.bg_color)

        # Variables
        self.input_path = tk.StringVar()
        self.output_name = tk.StringVar()
        self.profanity_level = tk.StringVar(value="moderate")
        self.num_passes = tk.IntVar(value=2)
        self.processing = False

        # Initialize ProfanityFilter
        self.pf = ProfanityFilter()

        self.create_widgets()

    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self.root, bg=self.accent_color, height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="CounterCurse",
            font=("Gorgia", 28, "bold"),
            bg=self.accent_color,
            fg="white"
        )
        title_label.pack(expand=True)


        # Main content frame
        content_frame = tk.Frame(self.root, bg=self.bg_color)
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Input video section
        input_label = tk.Label(
            content_frame,
            text="Input Video",
            font=("Gorgia", 12, "bold"),
            bg=self.bg_color,
            fg="#333"
        )
        input_label.pack(anchor="w", pady=(0, 5))

        input_frame = tk.Frame(content_frame, bg=self.bg_color)
        input_frame.pack(fill="x", pady=(0, 20))

        self.input_entry = tk.Entry(
            input_frame,
            textvariable=self.input_path,
            font=("Gorgia", 10),
            relief="solid",
            bd=1
        )
        self.input_entry.pack(side="left", fill="x", expand=True, ipady=8)

        browse_btn = tk.Button(
            input_frame,
            text="Browse",
            command=self.browse_input,
            bg=self.button_color,
            fg="white",
            font=("Gorgia", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8
        )
        browse_btn.pack(side="left", padx=(10, 0))
        self.bind_hover(browse_btn)

        # Output name section
        output_label = tk.Label(
            content_frame,
            text="Output Video Name",
            font=("Gorgia", 12, "bold"),
            bg=self.bg_color,
            fg="#333"
        )
        output_label.pack(anchor="w", pady=(0, 5))

        output_frame = tk.Frame(content_frame, bg=self.bg_color)
        output_frame.pack(fill="x", pady=(0, 20))

        self.output_entry = tk.Entry(
            output_frame,
            textvariable=self.output_name,
            font=("Gorgia", 10),
            relief="solid",
            bd=1
        )
        self.output_entry.pack(side="left", fill="x", expand=True, ipady=8)

        ext_label = tk.Label(
            output_frame,
            text=".mp4",
            font=("Gorgia", 10),
            bg=self.bg_color,
            fg="#666"
        )
        ext_label.pack(side="left", padx=(5, 0))

        # Profanity level section
        level_label = tk.Label(
            content_frame,
            text="Censoring Level",
            font=("Gorgia", 12, "bold"),
            bg=self.bg_color,
            fg="#333"
        )
        level_label.pack(anchor="w", pady=(0, 10))

        level_frame = tk.Frame(content_frame, bg=self.bg_color)
        level_frame.pack(fill="x", pady=(0, 20))

        levels = [
            ("Minor", "minor", "Basic profanity"),
            ("Moderate", "moderate", "Common curse words"),
            ("Strict", "strict", "Most inappropriate language")
        ]

        for i, (text, value, desc) in enumerate(levels):
            rb_frame = tk.Frame(level_frame, bg=self.bg_color)
            rb_frame.pack(side="left", expand=True, fill="x")

            rb = tk.Radiobutton(
                rb_frame,
                text=text,
                variable=self.profanity_level,
                value=value,
                font=("Gorgia", 10, "bold"),
                bg=self.bg_color,
                fg="#333",
                selectcolor=self.bg_color,
                activebackground=self.bg_color,
                cursor="hand2"
            )
            rb.pack(anchor="w")

            desc_label = tk.Label(
                rb_frame,
                text=desc,
                font=("Gorgia", 8),
                bg=self.bg_color,
                fg="#666"
            )
            desc_label.pack(anchor="w", padx=(20, 0))

        # Number of passes section
        passes_label = tk.Label(
            content_frame,
            text="Number of Passes",
            font=("Gorgia", 12, "bold"),
            bg=self.bg_color,
            fg="#333"
        )
        passes_label.pack(anchor="w", pady=(0, 10))

        passes_frame = tk.Frame(content_frame, bg=self.bg_color)
        passes_frame.pack(fill="x", pady=(0, 20))

        self.passes_spinbox = tk.Spinbox(
            passes_frame,
            from_=1,
            to=5,
            textvariable=self.num_passes,
            font=("Gorgia", 10),
            width=10,
            relief="solid",
            bd=1
        )
        self.passes_spinbox.pack(side="left")

        passes_info = tk.Label(
            passes_frame,
            text="Multiple passes can catch words missed in the first pass",
            font=("Gorgia", 9),
            bg=self.bg_color,
            fg="#666"
        )
        passes_info.pack(side="left", padx=(10, 0))

        # Progress section
        self.progress_frame = tk.Frame(content_frame, bg=self.bg_color)
        self.progress_frame.pack(fill="x", pady=(0, 15))

        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=("Gorgia", 9),
            bg=self.bg_color,
            fg="#666"
        )
        self.progress_label.pack(anchor="w", pady=(0, 5))

        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            length=640
        )

        # Process button
        self.process_btn = tk.Button(
            content_frame,
            text="Start Processing",
            command=self.start_processing,
            bg="#5cff67",
            fg="white",
            font=("Gorgia", 13, "bold"),
            relief="flat",
            cursor="hand2",
            padx=40,
            pady=12
        )
        self.process_btn.pack(pady=(10, 0))
        self.bind_hover(self.process_btn, normal="#5cff67", hover="#99ffa0")

    def bind_hover(self, button, normal=None, hover=None):
        """Add hover effect to buttons"""
        if normal is None:
            normal = self.button_color
        if hover is None:
            hover = self.button_hover

        button.bind("<Enter>", lambda e: button.config(bg=hover))
        button.bind("<Leave>", lambda e: button.config(bg=normal))

    def browse_input(self):
        """Open file dialog to select input video"""
        filename = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.input_path.set(filename)
            # Auto-fill output name based on input
            if not self.output_name.get():
                base_name = Path(filename).stem
                self.output_name.set(f"{base_name}_censored")

    def validate_inputs(self):
        """Validate user inputs before processing"""
        if not self.input_path.get():
            messagebox.showerror("Error", "Please select an input video file.")
            return False

        if not os.path.exists(self.input_path.get()):
            messagebox.showerror("Error", "Input video file does not exist.")
            return False

        if not self.output_name.get():
            messagebox.showerror("Error", "Please enter an output video name.")
            return False

        return True

    def start_processing(self):
        """Start the video processing in a separate thread"""
        if not self.validate_inputs():
            return

        if self.processing:
            messagebox.showwarning("Warning", "Processing is already in progress.")
            return

        # Disable controls
        self.processing = True
        self.process_btn.config(state="disabled", text="Processing...")
        self.input_entry.config(state="disabled")
        self.output_entry.config(state="disabled")
        self.passes_spinbox.config(state="disabled")

        # Show progress bar
        self.progress_bar.pack(fill="x")
        self.progress_bar.start(10)
        self.progress_label.config(text="Initializing...")

        # Start processing thread
        thread = threading.Thread(target=self.process_video, daemon=True)
        thread.start()

    def process_video(self):
        try:
            input_video = self.input_path.get()
            output_video = self.output_name.get() + ".mp4"
            level = self.profanity_level.get()
            passes = self.num_passes.get()

            current_input = input_video
            success = False

            for pass_num in range(1, passes + 1):
                self.update_progress(f"Pass {pass_num}/{passes} - Processing...")

                # For the final pass, use the desired output name
                if pass_num == passes:
                    current_output = output_video
                else:
                    current_output = f"temp_pass_{pass_num}.mp4"

                success = self.pf.process_video(current_input, current_output, level)

                if success:
                    current_input = current_output
                else:
                    break

            # Clean up temporary files
            for i in range(1, passes):
                temp_file = f"temp_pass_{i}.mp4"
                if os.path.exists(temp_file):
                    os.remove(temp_file)

            # Show result
            if success:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success",
                    f"Video processed successfully!\n\nOutput saved to: {output_video}"
                ))
            else:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    "Video processing failed. Check console for details."
                ))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"An error occurred:\n{str(e)}"
            ))
        finally:
            # Re-enable controls
            self.root.after(0, self.reset_ui)

    def update_progress(self, text):
        """Update progress label from thread"""
        self.root.after(0, lambda: self.progress_label.config(text=text))

    def reset_ui(self):
        """Reset UI after processing"""
        self.processing = False
        self.process_btn.config(state="normal", text="Start Processing")
        self.input_entry.config(state="normal")
        self.output_entry.config(state="normal")
        self.passes_spinbox.config(state="normal")
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress_label.config(text="")


def main():
    root = tk.Tk()
    app = CurseCleanerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()