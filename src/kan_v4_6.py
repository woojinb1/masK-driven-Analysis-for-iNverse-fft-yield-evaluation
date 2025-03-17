from PIL import Image, ImageTk
import cv2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from alphashape import alphashape
from shapely.geometry import Polygon, MultiPolygon
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Combobox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import sys
import csv

# Concave Hull 그리기 및 넓이 계산
def draw_concave_hulls_with_overlay(real_image, fft_image, points, clusters, alpha, min_cluster_size, one_pixel_area, show_cluster_ids, unit):
    unique_clusters = np.unique(clusters)
    height, width = real_image.shape
    fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
    ax.imshow(real_image, cmap='gray', origin='upper', extent=[0, width, height, 0])

    colors = plt.cm.get_cmap("turbo", len(unique_clusters))
    areas = []

    for cluster_id in unique_clusters:
        if cluster_id == -1:
            continue

        cluster_points = points[clusters == cluster_id]
        if len(cluster_points) < min_cluster_size:
            continue

        try:
            hull_polygon = alphashape(cluster_points, alpha)
            if isinstance(hull_polygon, MultiPolygon):
                area = sum(poly.area for poly in hull_polygon.geoms) * one_pixel_area
                for poly in hull_polygon.geoms:
                    x, y = poly.exterior.xy
                    ax.plot(y, x, color=colors(cluster_id / len(unique_clusters)), linewidth=1)
            elif isinstance(hull_polygon, Polygon):
                area = hull_polygon.area * one_pixel_area
                x, y = hull_polygon.exterior.xy
                ax.plot(y, x, color=colors(cluster_id / len(unique_clusters)), linewidth=1)
            else:
                area = 0

            areas.append((cluster_id, area))

            if show_cluster_ids:
                cluster_center = cluster_points.mean(axis=0)
                ax.text(
                    cluster_center[1], cluster_center[0],
                    f"ID: {cluster_id}",
                    color="black",
                    fontsize=8,
                    ha='center',
                    va='center',
                    bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white", alpha=0.7)
                )
        except Exception as e:
            print(f"Error processing cluster {cluster_id}: {e}")

    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig, areas

# 파일 열기 및 이미지 로드
def load_real_image():
    global real_image_path
    image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.bmp;*.jpg;*.jpeg;*.png")])
    if image_path:
        real_image_path = image_path

def load_inverse_fft_image():
    global inverse_fft_image_path
    image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.bmp;*.jpg;*.jpeg;*.png")])
    if image_path:
        inverse_fft_image_path = image_path

# Apply 버튼으로 이미지 업데이트
def apply_changes():
    global real_image_path, inverse_fft_image_path, canvas, area_listbox, current_figure, cluster_areas
    try:
        threshold = int(slider_threshold.get())
        eps = float(slider_eps.get())
        min_samples = int(slider_min_samples.get())
        alpha = float(slider_alpha.get())

        try:
            min_cluster_size = int(entry_min_cluster_size.get())
        except ValueError:
            messagebox.showwarning("Invalid Input", "Min Cluster Size must be an integer.")
            return

        try:
            one_pixel_area = float(entry_1_Pixel_Area.get())
            unit = pixel_area_unit_var.get()

            if unit == "um^2":
                one_pixel_area *= 1e6  # Convert um^2 to nm^2
        except ValueError:
            messagebox.showwarning("Invalid Input", "A pixel area must be a float.")
            return

        if not real_image_path or not os.path.exists(real_image_path):
            messagebox.showwarning("File Error", "Invalid or missing real image file.")
            return
        if not inverse_fft_image_path or not os.path.exists(inverse_fft_image_path):
            messagebox.showwarning("File Error", "Invalid or missing FFT image file.")
            return

        real_image = cv2.imread(real_image_path, cv2.IMREAD_GRAYSCALE)
        fft_image = cv2.imread(inverse_fft_image_path, cv2.IMREAD_GRAYSCALE)
        _, binary_image = cv2.threshold(fft_image, threshold, 255, cv2.THRESH_BINARY)
        points = np.column_stack(np.where(binary_image == 255))

        if len(points) == 0:
            messagebox.showwarning("No Points", "No points found in the binary image.")
            return

        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        clusters = dbscan.fit_predict(points)

        show_cluster_ids = cluster_id_var.get()  # Checkbutton 상태 확인
        fig, areas = draw_concave_hulls_with_overlay(
            real_image, fft_image, points, clusters, alpha, min_cluster_size, one_pixel_area, show_cluster_ids, unit
        )
        current_figure = fig
        cluster_areas = areas  # Save cluster areas for export

        for widget in result_frame.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=result_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack()
        canvas.draw()

        area_listbox.delete(0, tk.END)
        total_area = 0
        for cluster_id, area in areas:
            total_area += area
            area_listbox.insert(tk.END, f"Cluster {cluster_id}: Area = {area:.2f} {unit}")

        # 총 넓이를 표시
        area_listbox.insert(tk.END, "")  # 빈 줄 추가
        area_listbox.insert(tk.END, f"Total Area: {total_area:.2f} {unit}")

        # 총 넓이를 cluster_areas에 추가
        cluster_areas.append(("Total", total_area))

    except Exception as e:
        messagebox.showerror("Error", f"Error processing image: {e}")

# 오버레이된 이미지 저장 함수
def export_overlay():
    global current_figure, real_image_path
    if current_figure is None:
        messagebox.showwarning("No Image", "No overlayed image to save.")
        return

    default_filename = os.path.splitext(os.path.basename(real_image_path))[0] + "_overlay.png"
    file_path = filedialog.asksaveasfilename(
        initialfile=default_filename,
        defaultextension=".png",
        filetypes=[("PNG Files", "*.png"), ("JPEG Files", "*.jpg"), ("All Files", "*.*")],
        title="Save Overlay Image"
    )
    if file_path:
        try:
            real_image = cv2.imread(real_image_path, cv2.IMREAD_GRAYSCALE)
            height, width = real_image.shape
            dpi = 100
            current_figure.set_size_inches(width / dpi, height / dpi)
            current_figure.savefig(file_path, dpi=dpi, bbox_inches='tight', pad_inches=0)
            messagebox.showinfo("Saved", f"Image saved successfully at {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving the image: {e}")

# 넓이 리스트를 CSV로 저장하는 함수
def export_to_csv():
    global cluster_areas, real_image_path
    if not cluster_areas:
        messagebox.showwarning("No Data", "No cluster areas to save.")
        return

    default_filename = os.path.splitext(os.path.basename(real_image_path))[0] + "_areas.csv"
    file_path = filedialog.asksaveasfilename(
        initialfile=default_filename,
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        title="Save Cluster Areas as CSV"
    )
    if file_path:
        try:
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Cluster ID", "Area"])
                for cluster_id, area in cluster_areas:
                    writer.writerow([cluster_id, area])
            messagebox.showinfo("Saved", f"Cluster areas saved successfully at {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving the CSV file: {e}")

# 슬라이더 값 증가/감소 함수
def increment_slider(slider, step):
    current_value = slider.get()
    slider.set(current_value + step)

def decrement_slider(slider, step):
    current_value = slider.get()
    slider.set(current_value - step)

def resource_path(relative_path):
    """PyInstaller가 생성한 실행 파일 내에서 리소스 경로를 반환"""
    try:
        # PyInstaller에서 실행되는 경우
        base_path = sys._MEIPASS
    except AttributeError:
        # 개발 환경에서 실행되는 경우
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

root = tk.Tk()
root.title("kan v4.6")

real_image_path = None
inverse_fft_image_path = None
current_figure = None
cluster_areas = []

# 프로그램 설명 및 이미지 추가
header_frame = tk.Frame(root)
header_frame.pack(pady=10)

# 이미지 삽입
try:
    image_path = resource_path("bear.png")
    image = Image.open(image_path)
    image = image.resize((100, 100))
    photo_left = ImageTk.PhotoImage(image)

    flipped_image = image.transpose(Image.FLIP_LEFT_RIGHT)
    photo_right = ImageTk.PhotoImage(flipped_image)

    left_logo_label = tk.Label(header_frame, image=photo_right)
    left_logo_label.pack(side="left", padx=10)
    right_logo_label = tk.Label(header_frame, image=photo_left)
    right_logo_label.pack(side="right", padx=10)

except Exception as e:
    left_logo_label = tk.Label(header_frame, text="[Image Not Found]", fg="red")
    left_logo_label.pack(side="left", padx=10)
    right_logo_label = tk.Label(header_frame, text="[Image Not Found]", fg="red")
    right_logo_label.pack(side="right", padx=10)

# 설명 텍스트를 가운데 정렬 및 볼드체로 설정
description_text = tk.Text(
    header_frame,
    wrap="word",
    width=100,
    height=5,
    font=("Helvetica", 8),
    bg=root.cget("bg"),  # 배경색을 루트창과 동일하게 설정
    bd=0,
    highlightthickness=0
)
description_text.pack()

# 텍스트 추가
description_text.insert("1.0", "masK-driven Analysis for iNverse fft yield evaluation\n")
description_text.insert("2.0", "This tool analyzes images, detects contours, and calculates crystallized region.\n")
description_text.insert("3.0", "Made by WJB\n")

# 가운데 정렬 태그 설정
description_text.tag_configure("center", justify="center")

# 볼드 스타일 태그 설정
description_text.tag_configure("bold", font=("Helvetica", 12, "bold"))
description_text.tag_configure("bolds", font=("Helvetica", 14, "bold"))

# 텍스트에 태그 적용
description_text.tag_add("bolds", "1.0", "1.end")
description_text.tag_add("center", "1.0", "3.end")
description_text.tag_add("bold", "3.0", "3.end")

# 텍스트 수정 방지
description_text.configure(state="disabled")



# 텍스트 수정 방지
description_text.configure(state="disabled")



# 좌측 프레임
left_frame = tk.Frame(root)
left_frame.pack(side="left", padx=10, pady=10, fill="y")

# 우측 프레임
right_frame = tk.Frame(root)
right_frame.pack(side="right", padx=10, pady=10, fill="both", expand=True)

# 파일 선택 버튼
btn_frame = tk.Frame(left_frame)
btn_frame.pack(pady=10)
load_real_btn = tk.Button(btn_frame, text="Load Real Image", command=load_real_image, bg="lightblue", font=("Helvetica", 12))
load_real_btn.pack(side="left", padx=10)
load_inverse_fft_btn = tk.Button(btn_frame, text="Load Inverse FFT Image", command=load_inverse_fft_image, bg="lightblue", font=("Helvetica", 12))
load_inverse_fft_btn.pack(side="right", padx=10)

# 슬라이더 프레임
slider_frame = tk.Frame(left_frame)
slider_frame.pack(pady=10)

# Threshold 슬라이더
threshold_frame = tk.Frame(slider_frame)
threshold_frame.pack(fill="x")
tk.Label(threshold_frame, text="Threshold (0-255):").pack(side="left", padx=5)
slider_threshold = tk.Scale(threshold_frame, from_=0, to=255, orient="horizontal")
slider_threshold.set(45)
slider_threshold.pack(side="left", fill="x", expand=True)
thresh_inc_btn = tk.Button(threshold_frame, text="+", command=lambda: increment_slider(slider_threshold, 1))
thresh_inc_btn.pack(side="right")
thresh_dec_btn = tk.Button(threshold_frame, text="-", command=lambda: decrement_slider(slider_threshold, 1))
thresh_dec_btn.pack(side="right")

# eps 슬라이더
eps_frame = tk.Frame(slider_frame)
eps_frame.pack(fill="x")
tk.Label(eps_frame, text="eps (0-20):").pack(side="left", padx=5)
slider_eps = tk.Scale(eps_frame, from_=0, to=20, resolution=0.1, orient="horizontal")
slider_eps.set(11)
slider_eps.pack(side="left", fill="x", expand=True)
eps_inc_btn = tk.Button(eps_frame, text="+", command=lambda: increment_slider(slider_eps, 0.1))
eps_inc_btn.pack(side="right")
eps_dec_btn = tk.Button(eps_frame, text="-", command=lambda: decrement_slider(slider_eps, 0.1))
eps_dec_btn.pack(side="right")

# min_samples 슬라이더
min_samples_frame = tk.Frame(slider_frame)
min_samples_frame.pack(fill="x")
tk.Label(min_samples_frame, text="min_samples (0-100):").pack(side="left", padx=5)
slider_min_samples = tk.Scale(min_samples_frame, from_=1, to=100, orient="horizontal")
slider_min_samples.set(30)
slider_min_samples.pack(side="left", fill="x", expand=True)
min_samples_inc_btn = tk.Button(min_samples_frame, text="+", command=lambda: increment_slider(slider_min_samples, 1))
min_samples_inc_btn.pack(side="right")
min_samples_dec_btn = tk.Button(min_samples_frame, text="-", command=lambda: decrement_slider(slider_min_samples, 1))
min_samples_dec_btn.pack(side="right")

# alpha 슬라이더
alpha_frame = tk.Frame(slider_frame)
alpha_frame.pack(fill="x")
tk.Label(alpha_frame, text="alpha (0-1):").pack(side="left", padx=5)
slider_alpha = tk.Scale(alpha_frame, from_=0.01, to=1.0, resolution=0.01, orient="horizontal")
slider_alpha.set(0.2)
slider_alpha.pack(side="left", fill="x", expand=True)
alpha_inc_btn = tk.Button(alpha_frame, text="+", command=lambda: increment_slider(slider_alpha, 0.01))
alpha_inc_btn.pack(side="right")
alpha_dec_btn = tk.Button(alpha_frame, text="-", command=lambda: decrement_slider(slider_alpha, 0.01))
alpha_dec_btn.pack(side="right")

# 1_pixel_area 텍스트 입력 및 단위 선택
pixel_area_frame = tk.Frame(slider_frame)
pixel_area_frame.pack(fill="x", pady=5)

label_1_pixel_area = tk.Label(pixel_area_frame, text="1_pixel_area:")
label_1_pixel_area.pack(side="left", padx=5)
entry_1_Pixel_Area = tk.Entry(pixel_area_frame, width=10)
entry_1_Pixel_Area.insert(0, "0.001764")
entry_1_Pixel_Area.pack(side="left", padx=5)

pixel_area_unit_var = tk.StringVar(value="nm²")
pixel_area_unit_combobox = Combobox(pixel_area_frame, textvariable=pixel_area_unit_var, state="readonly")
pixel_area_unit_combobox["values"] = ["nm²", "µm²"]
pixel_area_unit_combobox.pack(side="left", padx=5)

# Min Cluster Size 텍스트 입력 필드
tk.Label(slider_frame, text="Min Cluster Size:").pack(anchor="w")
entry_min_cluster_size = tk.Entry(slider_frame)
entry_min_cluster_size.insert(0, "150")
entry_min_cluster_size.pack(fill="x")

cluster_id_var = tk.BooleanVar(value=True)
cluster_id_checkbutton = tk.Checkbutton(
    left_frame, text="Show Cluster IDs", variable=cluster_id_var, font=("Helvetica", 12)
)
cluster_id_checkbutton.pack(pady=5)

# Apply 버튼
apply_btn = tk.Button(left_frame, text="Apply", command=apply_changes, bg="lightblue", font=("Helvetica", 12))
apply_btn.pack(pady=10)

# 넓이 리스트 표시
tk.Label(left_frame, text="Cluster Areas:", font=("Helvetica", 14, "bold")).pack(pady=5)
area_listbox = tk.Listbox(left_frame, width=30, height=10)
area_listbox.pack(pady=5)

# Export 버튼
export_btn = tk.Button(left_frame, text="Export Image", command=export_overlay, bg="lightblue", font=("Helvetica", 12))
export_btn.pack(pady=5)

export_csv_btn = tk.Button(left_frame, text="Export CSV", command=export_to_csv, bg="lightblue", font=("Helvetica", 12))
export_csv_btn.pack(pady=5)

# 결과 이미지 표시 프레임
tk.Label(right_frame, text="Overlayed Image:", font=("Helvetica", 14, "bold")).pack(pady=5)
result_frame = tk.Frame(right_frame)
result_frame.pack(fill="both", expand=True)

root.mainloop()
