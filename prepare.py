import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import cv2
import PIL.Image, PIL.ImageTk

class VideoEditor:
    app_title = "Interface de Découpe Vidéo"
    
    app_width = 1280
    app_height = 720
    app_padding = 10

    app_play_on_load = True
    app_default_speed = 1

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(self.app_title)
        self.root.geometry('%dx%d+%d+%d' % (
            self.app_width,
            self.app_height,
            (app.winfo_screenwidth() - self.app_width) / 2,
            (app.winfo_screenheight() - self.app_height) / 2
        ))
        
        self.is_playing = False
        self.update_id = None
        self.frame = None

        # Build the user interface
        self.build_ui()


    def build_ui(self):
        # Créez un panneau
        self.pw = tk.PanedWindow(orient=tk.VERTICAL, sashwidth=10)

        # Top panel
        def build_top_panel(self):
            # (Hauteur initiale en 16:9)
            self.top_panel = tk.Frame(self.pw)

            self.top_panel.config(height=self.app_height // 2, bg="black")

            # Ajoutez le panneau supérieur au panneau principal
            self.pw.add(self.top_panel)
        
        # Bottom panel
        def build_bottom_panel(self):
            self.bottom_panel = tk.PanedWindow(self.pw, orient=tk.HORIZONTAL, sashrelief="flat")

            ## Left Pannel
            def build_left_frame(self):
                self.bottom_left_frame = tk.Frame(self.bottom_panel, padx=self.app_padding, pady=self.app_padding)
                self.top_slider = tk.Scale(self.bottom_left_frame, from_=0, to=100, orient="vertical", label="Haut", command=lambda _: self.update_video() if self.frame is not None and not self.is_playing else None)
                self.top_slider.grid(row=0, column=0)
               
                self.bottom_slider = tk.Scale(self.bottom_left_frame, from_=0, to=100, orient="vertical", label="Bas", command=lambda _: self.update_video() if self.frame is not None and not self.is_playing else None)
                self.bottom_slider.set(100)
                self.bottom_slider.grid(row=0, column=1)
                
                self.left_slider = tk.Scale(self.bottom_left_frame, from_=0, to=100, orient="horizontal", label="Gauche", command=lambda _: self.update_video() if self.frame is not None and not self.is_playing else None)
                self.left_slider.grid(row=2, column=0)
               
                self.right_slider = tk.Scale(self.bottom_left_frame, from_=0, to=100, orient="horizontal", label="Droite", command=lambda _: self.update_video() if self.frame is not None and not self.is_playing else None)
                self.right_slider.set(100)
                self.right_slider.grid(row=3, column=0)
               
                self.bottom_left_frame.grid(row=0, column=0)

            ## Right pannel
            def build_right_frame(self):
                self.bottom_right_frame = tk.Frame(self.bottom_panel, padx=self.app_padding, pady=self.app_padding)
                
                self.open_button = tk.Button(self.bottom_right_frame, text="Ouvrir la vidéo", command=self.open_video)
                self.open_button.pack()

                self.play_pause_button = tk.Button(self.bottom_right_frame, text="Play", state="disabled", command=self.toggle_play_pause)
                self.play_pause_button.pack()

                self.play_speed = tk.Scale(self.bottom_right_frame, from_=1, to=32, resolution=1, orient="horizontal", label="Vitesse")
                self.play_speed.set(self.app_default_speed)  # Valeur initiale de la vitesse
                self.play_speed.pack()

                self.bottom_right_frame.grid(row=0, column=1)

            # Build left/right frames
            build_left_frame(self)
            build_right_frame(self)

            # Ajoutez le panneau inférieur au panneau principal
            self.pw.add(self.bottom_panel)

        # Build panels
        build_top_panel(self)
        build_bottom_panel(self)

        self.pw.pack(fill=tk.BOTH, expand=True)

    def open_video(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.cap = cv2.VideoCapture(file_path)
            _, self.frame = self.cap.read()
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)

            self.video_label = tk.Label(self.top_panel)
            self.video_label.pack()

            self.toggle_play_pause()

            # Activation des boutons
            self.top_slider.config(state="normal")
            self.bottom_slider.config(state="normal")
            self.left_slider.config(state="normal")
            self.right_slider.config(state="normal")
            self.play_pause_button.config(state="normal")

            self.update_video()

    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        
        if self.is_playing:
            self.play_pause_button.config(text="Pause")
            self.update_video()
        else:
            self.play_pause_button.config(text="Play")

    def resize_to_fit_container(self, frame, container_width, container_height):
        frame_height, frame_width, _ = frame.shape
        aspect_ratio = frame_width / frame_height

        if container_width / aspect_ratio > container_height:
            new_width = int(container_height * aspect_ratio)
            new_height = container_height
        else:
            new_width = container_width
            new_height = int(container_width / aspect_ratio)

        if new_width > 0 and new_height > 0:
            resized_frame = cv2.resize(frame, (new_width, new_height))
            return resized_frame
        else:
            return frame
        
    def get_frame(self):
        _, frame = self.cap.read()

        return frame

    def update_video(self):
        if self.update_id:  # Si une tâche planifiée existe, annulez-la
            self.video_label.after_cancel(self.update_id)

        if self.is_playing:
            self.original_frame = self.get_frame()
            
        self.frame = self.original_frame
    
        if self.frame is not None:
            # Ajustez la taille de la vidéo pour remplir le conteneur tout en conservant le rapport d'aspect
            container_width = self.video_label.winfo_width()
            container_height = self.video_label.winfo_height()

            self.frame = self.resize_to_fit_container(self.frame, container_width, container_height)

            self.update_rectangle()
            
            photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)))

            self.video_label.config(image=photo)
            self.video_label.image = photo

            if self.is_playing:
                # Calculer l'intervalle en fonction de la vitesse en images par seconde (IPS)
                speed = self.fps * self.play_speed.get()
                refresh_interval = int(1000 / speed) if speed > 0 else 1000

                self.update_id = self.video_label.after(refresh_interval, self.update_video)

    def update_rectangle(self):
        # Obtenez les positions des curseurs
        top_pos = self.top_slider.get()
        bottom_pos = self.bottom_slider.get()
        left_pos = self.left_slider.get()
        right_pos = self.right_slider.get()

        top = min(top_pos, bottom_pos) * self.frame.shape[0] / 100
        bottom = max(top_pos, bottom_pos) * self.frame.shape[0] / 100
        left = min(left_pos, right_pos) * self.frame.shape[1] / 100
        right = max(left_pos, right_pos) * self.frame.shape[1] / 100

        color = [0, 255, 0]
        thickness = 4

        self.frame[int(top):int(bottom), int(left):int(left+thickness)] = color
        self.frame[int(top):int(bottom), int(right-thickness):int(right)] = color
        self.frame[int(top):int(top+thickness), int(left):int(right)] = color
        self.frame[int(bottom-thickness):int(bottom), int(left):int(right)] = color

if __name__ == "__main__":
    app = tk.Tk()
    editor = VideoEditor(app)
    app.mainloop()
