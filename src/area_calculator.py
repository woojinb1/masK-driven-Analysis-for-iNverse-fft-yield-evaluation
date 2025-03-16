import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class ImagePolygonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Polygon Area Calculator")

        # 윈도우 크기 조정 가능
        self.root.geometry("800x600")

        # 이미지 프레임
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 버튼 프레임
        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack()

        self.upload_btn = tk.Button(self.btn_frame, text="Upload Image", command=self.upload_image)
        self.upload_btn.pack(side=tk.LEFT)

        self.calculate_btn = tk.Button(self.btn_frame, text="Calculate Area", command=self.calculate_area, state=tk.DISABLED)
        self.calculate_btn.pack(side=tk.LEFT)

        self.delete_btn = tk.Button(self.btn_frame, text="Delete Previous Dot", command=self.delete_previous_dot, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT)

        self.clear_btn = tk.Button(self.btn_frame, text="Clear Points", command=self.clear_points, state=tk.DISABLED)
        self.clear_btn.pack(side=tk.LEFT)

        # 픽셀당 실제 넓이 입력
        self.pixel_area_frame = tk.Frame(root)
        self.pixel_area_frame.pack()

        self.pixel_area_label = tk.Label(self.pixel_area_frame, text="Area per Pixel:")
        self.pixel_area_label.pack(side=tk.LEFT)

        self.pixel_area_entry = tk.Entry(self.pixel_area_frame, width=10)
        self.pixel_area_entry.pack(side=tk.LEFT)
        self.pixel_area_entry.insert(0, "1.0")

        # 초기 변수 설정
        self.points = []
        self.point_ids = []
        self.image = None
        self.image_tk = None
        self.original_width = 0
        self.original_height = 0
        self.display_width = 0
        self.display_height = 0
        self.polygon = None
        self.area_text_id = None

        # 마우스 이벤트 바인딩
        self.canvas.bind("<Button-1>", self.add_point)

        # 창 크기 변경 시 캔버스 크기 조정
        self.root.bind("<Configure>", self.resize_canvas)

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
        if file_path:
            self.image = Image.open(file_path)
            self.original_width, self.original_height = self.image.size  # 원본 크기 저장

            self.update_image_display()

            # 초기화
            self.points.clear()
            self.point_ids.clear()
            self.canvas.delete("all")
            self.calculate_btn.config(state=tk.DISABLED)
            self.clear_btn.config(state=tk.DISABLED)
            self.delete_btn.config(state=tk.DISABLED)
            self.polygon = None
            self.area_text_id = None

    def update_image_display(self):
        """ 현재 캔버스 크기에 맞춰 비율을 유지하며 이미지 크기를 조정 """
        if not self.image:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width == 1 or canvas_height == 1:  # 창이 열릴 때 초기 크기가 1로 설정되는 경우 방지
            return

        # 비율 유지하면서 크기 조정
        img_ratio = self.original_width / self.original_height
        canvas_ratio = canvas_width / canvas_height

        if img_ratio > canvas_ratio:
            self.display_width = canvas_width
            self.display_height = int(canvas_width / img_ratio)
        else:
            self.display_height = canvas_height
            self.display_width = int(canvas_height * img_ratio)

        resized_img = self.image.resize((self.display_width, self.display_height), Image.LANCZOS)
        self.image_tk = ImageTk.PhotoImage(resized_img)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)

    def resize_canvas(self, event):
        """ 창 크기 변경 시 캔버스 크기를 다시 설정 """
        self.update_image_display()

    def add_point(self, event):
        """ 이미지 상 클릭된 좌표를 원본 이미지 기준으로 변환 후 저장 """
        if self.image:
            x_ratio = self.original_width / self.display_width
            y_ratio = self.original_height / self.display_height

            orig_x = event.x * x_ratio
            orig_y = event.y * y_ratio

            self.points.append((orig_x, orig_y))
            dot = self.canvas.create_oval(event.x - 3, event.y - 3, event.x + 3, event.y + 3, fill="red", outline="red")
            self.point_ids.append(dot)

            if len(self.points) >= 3:
                self.calculate_btn.config(state=tk.NORMAL)
            self.clear_btn.config(state=tk.NORMAL)
            self.delete_btn.config(state=tk.NORMAL)

    def delete_previous_dot(self):
        if self.points:
            self.points.pop()
            self.canvas.delete(self.point_ids.pop())

            if len(self.points) < 3:
                self.calculate_btn.config(state=tk.DISABLED)
            if not self.points:
                self.clear_btn.config(state=tk.DISABLED)
                self.delete_btn.config(state=tk.DISABLED)

    def calculate_area(self):
        if len(self.points) < 3:
            messagebox.showwarning("Warning", "At least 3 points are required to form a polygon.")
            return

        try:
            pixel_area = float(self.pixel_area_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid pixel area input. Please enter a numeric value.")
            return

        x_coords, y_coords = zip(*self.points)

        area_px = 0.5 * abs(sum(x * y_next for x, y_next in zip(x_coords, y_coords[1:] + (y_coords[0],))) -
                             sum(y * x_next for y, x_next in zip(y_coords, x_coords[1:] + (x_coords[0],))))

        area_actual = area_px * pixel_area

        if self.polygon:
            self.canvas.delete(self.polygon)

        display_points = [(x / (self.original_width / self.display_width), 
                           y / (self.original_height / self.display_height)) for x, y in self.points]

        self.polygon = self.canvas.create_polygon(display_points, outline="blue", fill="blue", stipple="gray50")

        if self.area_text_id:
            self.canvas.delete(self.area_text_id)

        self.area_text_id = self.canvas.create_text(
            self.display_width // 2, self.display_height - 20,
            text=f"Area: {area_actual:.2f} units²",
            fill="red", font=("Arial", 16, "bold")
        )

    def clear_points(self):
        self.points.clear()
        self.point_ids.clear()
        self.canvas.delete("all")
        if self.image_tk:
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)
        self.calculate_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImagePolygonApp(root)
    root.mainloop()
