#!/usr/bin/env python3

"""
🗨️ HardSubHunter
Author: Clément Moine
Email: clement.moine86@gmail.com
GitHub: https://github.com/clementmoine
Discord: clement.moine
LinkedIn: https://www.linkedin.com/in/clemmoine/
License: MIT License (see below)

This tool allows you to open a video, define a cropping area, and then analyze it to extract hard-subtitles using Tesseract, saving them to an SRT file.

License:
The MIT License (MIT)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS," WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
import cv2
import numpy as np
import PIL.Image, PIL.ImageTk


class VideoEditor:
    def __init__(self, root: tk.Tk):
        # Initialize the interface
        self.root = root
        self.app_title = "🗨️ HardSubHunter"
        self.app_width, self.app_height, self.app_padding = 1280, 720, 10
        self.app_play_on_load = True
        self.app_default_speed = 1

        # Variables for video management
        self.ignore_next_timeline_change = False
        self.is_playing = False
        self.update_id = None
        self.cap, self.frame, self.fps, self.frameCount = None, None, None, None
        self.original_frame = None  # Initialize original_frame

        # Initialize UI elements to None
        self.video_label = None
        self.timeline = None
        self.top_slider = None
        self.bottom_slider = None
        self.left_slider = None
        self.right_slider = None
        self.play_pause_button = None
        self.play_speed = None
        self.bottom_panel = None

        # Build the user interface
        self.build_ui()
        self.create_menu(root)

    def build_ui(self):
        # Configure the main window
        self.root.title(self.app_title)
        self.root.geometry(
            f"{self.app_width}x{self.app_height}+{(self.root.winfo_screenwidth() - self.app_width) // 2}+{(self.root.winfo_screenheight() - self.app_height) // 2}"
        )

        # Create a main pane
        self.pw = ttk.PanedWindow(orient=tk.VERTICAL)
        self.pw.pack(fill=tk.BOTH, expand=True)

        # Build the top and bottom panels
        self.build_top_panel()
        self.build_bottom_panel()

    def create_menu(self, root):
        menubar = tk.Menu(root)
        root.config(menu=menubar)

        # Menu "File"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Video", command=self.open_video)
        file_menu.add_command(label="Exit", command=root.quit)

        # Menu "Help"
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about_dialog)

    def show_about_dialog(self):
        about_info = """
        🗨️ HardSubHunter
        Version 1.0
        Author: Clément Moine
        Discord: clement.moine
        License: MIT
        """
        simpledialog.messagebox.showinfo("About HardSubHunter", about_info)

    def create_frame(self, parent, padding=(0, 0), style=None, image=None):
        """Create a frame within a parent with an image (optional)."""
        frame = ttk.Frame(parent, padding=padding, style=style)
        frame.grid(row=0, column=0)

        return frame

    def create_slider(self, parent, command=None, from_=0, to=100, orient="horizontal", length=None):
        """Create a slider within a parent with a label and a callback command."""
        slider = ttk.Scale(
            parent,
            from_=from_,
            to=to,
            # label=label,
            orient=orient,
            length=length,
            command=command,
        )

        return slider

    def build_top_panel(self):
        """Build the top panel of the interface."""
        self.top_panel = self.create_frame(self.pw)

        self.top_panel.grid_rowconfigure(0, weight=1)
        self.top_panel.grid_columnconfigure(0, weight=1)

        self.video_label = tk.Label(
            self.top_panel,
            height=self.app_height // 2,
            image=PIL.ImageTk.PhotoImage(
                image=PIL.Image.new(
                    "RGB", (self.app_width, self.app_height // 2), (0, 0, 0)
                )
            ),
            background="black",
        )
        self.video_label.grid(row=0, column=0, sticky="nsew")

        self.timeline = self.create_slider(
            self.top_panel,
            orient="horizontal",
            from_=0,
            to=0,
            length=self.app_width,
            command=self.timeline_changed,
        )
        self.timeline.grid(row=1, column=0, sticky="ew")

        self.pw.add(self.top_panel)

    def build_left_frame(self):
        """Build the left frame of the bottom panel."""
        self.bottom_left_frame = self.create_frame(
            self.bottom_panel, padding=(self.app_padding, self.app_padding)
        )

        self.top_slider = self.create_slider(
            self.bottom_left_frame, lambda _: self.update_video()
        )
        self.top_slider.grid(row=0, column=0)

        self.bottom_slider = self.create_slider(
            self.bottom_left_frame, lambda _: self.update_video()
        )
        self.bottom_slider.grid(row=1, column=0)
        self.bottom_slider.set(100)

        self.left_slider = self.create_slider(
            self.bottom_left_frame, lambda _: self.update_video()
        )
        self.left_slider.grid(row=2, column=0)

        self.right_slider = self.create_slider(
            self.bottom_left_frame, lambda _: self.update_video()
        )
        self.right_slider.grid(row=3, column=0)
        self.right_slider.set(100)

        self.bottom_left_frame.grid(row=0, column=0)

    def build_right_frame(self):
        """Build the right frame of the bottom panel."""
        self.bottom_right_frame = self.create_frame(
            self.bottom_panel, padding=(self.app_padding, self.app_padding)
        )

        self.open_button = self.create_button(
            self.bottom_right_frame, text="Open Video", command=self.open_video
        )
        self.open_button.pack()

        self.play_pause_button = self.create_button(
            self.bottom_right_frame,
            text="Play",
            state="disabled",
            command=self.toggle_play_pause,
        )
        self.play_pause_button.pack()

        self.play_speed = self.create_slider(
            self.bottom_right_frame,
            from_=1,
            to=32,
            orient="horizontal",
        )
        self.play_speed.set(self.app_default_speed)
        self.play_speed.pack()

        self.bottom_right_frame.grid(row=0, column=1)

    def build_bottom_panel(self):
        """Build the bottom panel of the interface."""
        self.bottom_panel = ttk.PanedWindow(self.pw, orient=tk.HORIZONTAL)

        self.build_left_frame()
        self.build_right_frame()

        self.pw.add(self.bottom_panel)

    def create_button(self, parent, text, command, state="normal"):
        """Create a button with text, a callback command, and an optional state."""
        button = ttk.Button(parent, text=text, command=command, state=state)
        button.pack()

        return button

    def open_video(self):
        """Open a video from a file."""
        file_path = filedialog.askopenfilename()

        if file_path:
            self.cap = cv2.VideoCapture(file_path)
            _, self.frame = self.cap.read()
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.frameCount = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

            self.toggle_play_pause(True)

            self.enable_controls()

            self.timeline.config(to=self.frameCount)
            self.ignore_next_timeline_change = True
            self.timeline.set(0)

            self.update_video()

    def toggle_play_pause(self, expectedState=None):
        """Toggle between playing and pausing the video."""
        self.is_playing = (
            expectedState if expectedState is not None else not self.is_playing
        )
        self.play_pause_button.config(text="Pause" if self.is_playing else "Play")

        if self.is_playing:
            self.update_video()

    def enable_controls(self, state="normal"):
        """Enable or disable the interface controls."""
        self.top_slider.config(state=state)
        self.bottom_slider.config(state=state)
        self.left_slider.config(state=state)
        self.right_slider.config(state=state)
        self.play_pause_button.config(state=state)

    def get_frame(self):
        """Get a frame from the currently playing video."""
        _, frame = self.cap.read()

        frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))

        if self.timeline.get() != frame_number:
            self.ignore_next_timeline_change = True
            self.timeline.set(frame_number)

        return frame
    
    def timeline_changed(self, _=None):
        """Called when there is a change in the progress bar."""
        if self.cap and not self.ignore_next_timeline_change:
            frame_number = self.timeline.get()

            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.original_frame = self.get_frame()

            self.update_video()
        self.ignore_next_timeline_change = False

    def update_video(self):
        """Update the video display."""
        if self.update_id:
            self.video_label.after_cancel(self.update_id)

        if self.is_playing:
            self.original_frame = self.get_frame()

        self.update_play_speed_label()
        self.frame = self.original_frame

        container_width = self.video_label.winfo_width()
        container_height = self.video_label.winfo_height()

        if self.frame is not None:
            self.frame = self.resize_to_fit_container(
                self.frame, container_width, container_height
            )

        photo = PIL.ImageTk.PhotoImage(
            image=PIL.Image.fromarray(cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB))
            if self.frame is not None
            else PIL.Image.new("RGB", (container_width, container_height), (0, 0, 0))
        )

        photo = self.apply_rectangle(photo)

        self.video_label.config(image=photo)
        self.video_label.image = photo

        if self.is_playing:
            speed = self.fps * (self.play_speed.get() if self.play_speed else 0)

            refresh_interval = int(1000 / speed) if speed > 0 else 1000

            self.update_id = self.video_label.after(refresh_interval, self.update_video)

    def apply_rectangle(self, image: PIL.ImageTk.PhotoImage):
        """Apply a rectangle on the image based on the sliders."""
        if (
            self.top_slider
            and self.left_slider
            and self.bottom_slider
            and self.right_slider
        ):
            top_pos, bottom_pos = self.top_slider.get(), self.bottom_slider.get()
            left_pos, right_pos = self.left_slider.get(), self.right_slider.get()

            top = min(top_pos, bottom_pos) * image.height() / 100
            bottom = max(top_pos, bottom_pos) * image.height() / 100
            left = min(left_pos, right_pos) * image.width() / 100
            right = max(left_pos, right_pos) * image.width() / 100

            color, thickness = (0, 255, 0), 4

            img_array = PIL.ImageTk.getimage(image)

            if isinstance(img_array, PIL.Image.Image):
                img_array = np.array(img_array)

            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

            cv2.rectangle(
                img_array,
                (int(left), int(top)),
                (int(right - thickness), int(bottom - thickness)),
                color,
                thickness,
            )

            updated_image = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
            updated_image = PIL.Image.fromarray(updated_image)
            updated_photo = PIL.ImageTk.PhotoImage(updated_image)

            return updated_photo
        else:
            return image

    def resize_to_fit_container(self, frame, container_width, container_height):
        """Resize the image to fit in the container while maintaining the aspect ratio."""
        frame_height, frame_width, _ = frame.shape
        aspect_ratio = frame_width / frame_height

        if container_width / aspect_ratio > container_height:
            new_width, new_height = (
                int(container_height * aspect_ratio),
                container_height,
            )
        else:
            new_width, new_height = container_width, int(container_width / aspect_ratio)

        if new_width > 0 and new_height > 0:
            resized_frame = cv2.resize(frame, (new_width, new_height))

            return resized_frame
        else:
            return frame


if __name__ == "__main__":
    app = tk.Tk()
    editor = VideoEditor(app)
    app.mainloop()
