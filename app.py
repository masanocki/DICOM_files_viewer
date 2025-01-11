import pydicom
import numpy as np
import matplotlib.pylab as plt
import os
import customtkinter as ctk
import threading
from pathlib import Path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
        self.loading_files_label = ctk.CTkLabel(
            self,
            text="Loading scans...",
            font=ctk.CTkFont("Arial", 40),
        )
        self.loading_files_label.grid(row=0, column=0, pady=(0, 100))

        self.log_textbox = ctk.CTkTextbox(
            self, height=300, font=ctk.CTkFont("Arial", 17)
        )
        self.log_textbox.grid(
            row=0, column=0, pady=(350, 0), padx=(50, 50), sticky="ew"
        )
        self.log_textbox.insert("end", "Starting process...\n")
        self.log_textbox.configure(state="disabled")
        self.loading_progress_bar.set(0)
        self.load_files()

    def load_files(self):
        def loading_task():
            self.append_log("Scanning directory for DICOM files...")
            self.num_of_items = sum(
                1
                for root, _, filenames in os.walk(self.dir_path)
                for f in filenames
                if f.endswith(".dcm")
            )
            self.append_log(f"Found {self.num_of_items} DICOM files")
            self.append_log("Starting files load")
            self.iter_step = 1 / self.num_of_items
            self.progress_step = self.iter_step
            self.scans = []
            for root, _, filenames in os.walk("series-00000"):
                for filename in filenames:
                    dcm_path = Path(root, filename)
                    if dcm_path.suffix == ".dcm":
                        dicom = pydicom.dcmread(dcm_path)
                        self.scans.append(dicom)
                        self.append_log(f"Loaded file: {filename}")
                    self.progress_step += self.iter_step
                    self.loading_progress_bar.set(self.progress_step)
            self.append_log("File loading completed successfully")
            self.after(100, self.scans_conversion)

        threading.Thread(target=loading_task).start()

    def scans_conversion(self):
        self.loading_progress_bar.set(0)
        self.loading_files_label.configure(text="Converting scans to images...")
        self.append_log("Starting scan conversion to images...")

        def conversion_task():
            self.iter_step = 1 / self.num_of_items
            self.progress_step = self.iter_step
            images_list = []
            for i, scan in enumerate(self.scans):
                images_list.append(scan.pixel_array)
                self.append_log(f"Converted scan {i+1}/{self.num_of_items} to image")
                self.progress_step += self.iter_step
                self.loading_progress_bar.set(self.progress_step)
            self.images = np.stack(images_list)
            self.append_log("Scan conversion completed")
            self.after(100, self.hu_scale_conversion)

        threading.Thread(target=conversion_task).start()

    def hu_scale_conversion(self):
        self.loading_progress_bar.set(0)
        self.loading_files_label.configure(
            text="Converting images to Hounsfield Scale (HU)..."
        )
        self.append_log("Starting conversion to Hounsfield Units (HU)...")

        def hu_conversion_task():
            self.iter_step = 1 / self.num_of_items
            self.progress_step = self.iter_step
            hu_images = []
            for i, (image, scan) in enumerate(zip(self.images, self.scans)):
                intercept = scan.RescaleIntercept
                slope = scan.RescaleSlope
                hu_image = image * slope + intercept
                hu_images.append(hu_image.flatten())
                self.append_log(
                    f"Converted image {i+1}/{len(self.images)} to Hounsfield scale"
                )

                self.progress_step += self.iter_step
                self.loading_progress_bar.set(self.progress_step)

            self.hu_images = np.stack(hu_images)
            self.append_log("HU conversion completed")
            self.after(100, self.on_hu_conversion_complete)

        threading.Thread(target=hu_conversion_task).start()

    def on_hu_conversion_complete(self):
        self.loading_progress_bar.destroy()
        self.loading_files_label.destroy()
        self.log_textbox.destroy()

        self.grid_rowconfigure((0, 1), weight=1)
        self.grid_columnconfigure((0, 1), weight=1)

        self.canvas = ctk.CTkCanvas(self, bg="#1a1a1a", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.histogram_canvas = ctk.CTkCanvas(self, bg="#1a1a1a", highlightthickness=0)
        self.histogram_canvas.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.scrollbar = ctk.CTkScrollbar(
            self, orientation="horizontal", command=self.canvas.xview
        )
        self.scrollbar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(50, 50))

        self.canvas.configure(xscrollcommand=self.scrollbar.set)

        self.right_info_box = ctk.CTkTextbox(
            self,
            width=300,
            height=200,
            font=ctk.CTkFont("Arial", 25),
            fg_color="#1a1a1a",
        )
        self.right_info_box.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        self.left_legend_box = ctk.CTkTextbox(
            self,
            width=300,
            height=200,
            font=ctk.CTkFont("Arial", 25),
            fg_color="#1a1a1a",
        )
        self.left_legend_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        legend_text = (
            "\t\t\tBLACK -> Air (< -700 HU)\n"
            "\t\t\tYELLOW -> Fat (-80 do -100 HU)\n"
            "\t\t\tBLUE -> Water (0 +/- 5 HU)\n"
            "\t\t\tRED -> Blood (80 +/- 10 HU)\n"
            "\t\t\tPINK -> Muscles (~+40 HU)\n"
            "\t\t\tORANGE -> Contrast (~+130 HU)\n"
            "\t\t\tWHITE -> Bones (> +130 HU)\n"
        )
        self.left_legend_box.insert("1.0", legend_text)
        self.left_legend_box.configure(state="disabled")

        def update_image_and_histogram(index):
            ax_image.clear()
            current_image = self.hu_images[index].reshape(self.images[index].shape)

            # Color mapping based on HU values
            mapped_image = np.zeros_like(current_image, dtype=np.uint8)
            mapped_image[(current_image < -700)] = 0  # Air (black)
            mapped_image[(-100 <= current_image) & (current_image < -80)] = (
                1  # Fat (yellow)
            )
            mapped_image[(-5 <= current_image) & (current_image <= 5)] = (
                2  # Water (blue)
            )
            mapped_image[(70 <= current_image) & (current_image <= 90)] = (
                3  # Blood (red)
            )
            mapped_image[(30 <= current_image) & (current_image <= 50)] = (
                4  # Muscle (pink)
            )
            mapped_image[(120 <= current_image) & (current_image <= 140)] = (
                5  # Contrast (orange)
            )
            mapped_image[(current_image > 130)] = 6  # Bone (white)

            color_map = {
                0: "Air (black)",
                1: "Fat (yellow)",
                2: "Water (blue)",
                3: "Blood (red)",
                4: "Muscles (pink)",
                5: "Contrast (orange)",
                6: "Bones (white)",
            }

            # Convert mapped image to RGB for visualization
            rgb_image = np.zeros((*current_image.shape, 3), dtype=np.uint8)
            for key, color in color_map.items():
                if key == 0:  # Skip air for percentage calculation
                    continue
                rgb_image[mapped_image == key] = np.array(
                    {
                        1: [255, 255, 0],  # Yellow (Fat)
                        2: [0, 0, 255],  # Blue (Water)
                        3: [255, 0, 0],  # Red (Blood)
                        4: [255, 192, 203],  # Pink (Muscle)
                        5: [255, 165, 0],  # Orange (Contrast)
                        6: [255, 255, 255],  # White (Bone)
                    }[key],
                    dtype=np.uint8,
                )

            ax_image.imshow(rgb_image, cmap="gray")
            ax_image.set_title(f"Cross-section visualization", color="white")
            ax_image.set_axis_off()
            fig_image.canvas.draw_idle()

            # Count the occurrence of each tissue type, excluding air
            unique, counts = np.unique(mapped_image, return_counts=True)
            total_pixels = current_image.size - np.sum(
                mapped_image == 0
            )  # Exclude air pixels
            percentages = {
                color_map[key]: (counts[idx] / total_pixels) * 100
                for idx, key in enumerate(unique)
                if key != 0  # Exclude air
            }

            percentage_text = "\n".join(
                [
                    f"{tissue}: {percentages.get(tissue, 0):.2f}%"
                    for tissue in color_map.values()
                    if tissue != "Air (black)"
                ]
            )

            # Update the right info box with tissue percentages
            self.right_info_box.configure(state="normal")
            self.right_info_box.delete("1.0", "end")
            self.right_info_box.insert("1.0", percentage_text)
            self.right_info_box.configure(state="disabled")

            ax_histogram.clear()
            ax_histogram.hist(self.hu_images[index], bins=100, color="blue", alpha=0.7)
            ax_histogram.set_title("Histogram (HU)", color="white")
            ax_histogram.set_xlabel("Hounsfield Units (HU)")
            ax_histogram.xaxis.label.set_color("white")
            ax_histogram.tick_params(axis="x", colors="white")
            ax_histogram.spines["bottom"].set_color("white")
            ax_histogram.set_ylabel("Pixel count")
            ax_histogram.yaxis.label.set_color("white")
            ax_histogram.tick_params(axis="y", colors="white")
            ax_histogram.spines["left"].set_color("white")
            ax_histogram.spines[["right", "top"]].set_visible(False)
            fig_histogram.canvas.draw_idle()

        fig_image, ax_image = plt.subplots()
        ax_image.set_axis_off()
        ax_image.set_facecolor("#1a1a1a")
        fig_image.patch.set_facecolor("#1a1a1a")

        fig_histogram, ax_histogram = plt.subplots()
        ax_histogram.set_facecolor("#1a1a1a")
        fig_histogram.patch.set_facecolor("#1a1a1a")

        update_image_and_histogram(0)

        plot_widget_image = FigureCanvasTkAgg(fig_image, master=self.canvas)
        plot_widget_image.get_tk_widget().pack(side="top", fill="both", expand=True)
        plot_widget_image.get_tk_widget().configure(bg="#1a1a1a", highlightthickness=0)

        plot_widget_histogram = FigureCanvasTkAgg(
            fig_histogram, master=self.histogram_canvas
        )
        plot_widget_histogram.get_tk_widget().pack(side="top", fill="both", expand=True)
        plot_widget_histogram.get_tk_widget().configure(
            bg="#1a1a1a", highlightthickness=0
        )

        def on_scroll(action, value):
            if action == "moveto":
                index = int(float(value) * (len(self.images) - 1))
                update_image_and_histogram(index)
            elif action == "scroll":
                index = int(float(self.canvas.xview()[0]) * (len(self.images) - 1))
                update_image_and_histogram(index)

        self.scrollbar.configure(command=on_scroll)
        self.canvas.configure(scrollregion=(0, 0, len(self.images) * 100, 1))

    def append_log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
