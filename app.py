import pydicom
import numpy as np
import matplotlib.pylab as plt
import os
import customtkinter as ctk
from pathlib import Path

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class App(ctk.CTk):
    def __init__(self, fg_color=None, **kwargs):
        super().__init__(fg_color, **kwargs)
        self.win_height = self.winfo_screenheight()
        self.win_width = self.winfo_screenwidth()
        self.geometry(f"{self.win_width}x{self.win_height}")
        self.title("DICOM Viewer")
        self.start_screen()
        self.dir_path = None

    def start_screen(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.dir_path_label = ctk.CTkLabel(
            self,
            text="Input DICOM series directory path:",
            font=ctk.CTkFont("Arial", 30, weight="bold"),
        )
        self.dir_path_label.grid(row=0, column=0, pady=(0, 120))
        self.dir_path_entry = ctk.CTkEntry(
            self,
            placeholder_text="DICOM files folder path",
            width=700,
            height=50,
            font=ctk.CTkFont("Arial", 20),
        )
        self.dir_path_entry.grid(row=0, column=0)

        self.dir_path_button = ctk.CTkButton(
            self,
            text="Browse",
            command=self.browse_dir,
            height=50,
            font=ctk.CTkFont("Arial", 20),
        )
        self.dir_path_button.grid(row=0, column=0, padx=(880, 0))

        self.load_dir_button = ctk.CTkButton(
            self,
            text="Start",
            command=self.loading_screen,
            height=100,
            width=300,
            font=ctk.CTkFont("Arial", 30),
        )
        self.load_dir_button.grid(row=0, column=0, pady=(200, 0))

    def browse_dir(self):
        directory_path = ctk.filedialog.askdirectory()
        self.dir_path_entry.delete(0, "end")
        self.dir_path_entry.insert(0, directory_path)

    def loading_screen(self):
        self.dir_path = self.dir_path_entry.get()
        self.dir_path_label.destroy()
        self.dir_path_entry.destroy()
        self.dir_path_button.destroy()
        self.load_dir_button.destroy()

        self.loading_progress_bar = ctk.CTkProgressBar(
            self,
            orientation="horizontal",
            mode="determinate",
            height=25,
        )
        self.loading_progress_bar.grid(row=0, column=0, sticky="ew", padx=(50, 50))
        self.loading_progress_bar.set(0)
        self.load_files()

    def load_files(self):
        self.num_of_items = len(
            [
                f
                for f in os.listdir(self.dir_path)
                if os.path.isfile(os.path.join(self.dir_path, f))
            ]
        )

        self.iter_step = 1 / self.num_of_items
        self.progress_step = self.iter_step
        self.loading_progress_bar.start()
        self.scans = []
        for root, _, filenames in os.walk("series-00000"):
            for filename in filenames:
                self.loading_progress_bar.set(self.progress_step)
                self.progress_step += self.iter_step
                dcm_path = Path(root, filename)
                if dcm_path.suffix == ".dcm":
                    dicom = pydicom.dcmread(dcm_path)
                    self.scans.append(dicom)
                self.update_idletasks()
        self.loading_progress_bar.stop()

    def animate_scans(self, scans):
        plt.ion()
        graph = plt.imshow(scans[0].pixel_array)
        plt.pause(1)

        k = 1
        while True:
            graph.remove()
            graph = plt.imshow(scans[k].pixel_array)
            plt.pause(0.1)
            k = k + 1
            if k > 360:
                k = 1


# if __name__ == "__main__":


#     # KONWERSJA SKANOW DO OBRAZOW
#     image = np.stack([s.pixel_array for s in scans])

#     # KONWERSJA DO SKALI HOUNSEFIELDA (HU)
#     intercept = scans[0].RescaleIntercept
#     slope = scans[0].RescaleSlope
#     hu_scale = scans[0].pixel_array * slope + intercept
#     hu_values = hu_scale.flatten()

#     plt.figure(figsize=(10, 6))
#     plt.hist(hu_values)
#     plt.title("Histogram wartości pikseli w skali Hounsfielda (HU)")
#     plt.xlabel("Hounsfield Units (HU)")
#     plt.ylabel("Liczba pikseli")
#     plt.grid(axis="y", linestyle="--", alpha=0.7)
#     plt.show()
