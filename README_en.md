# masK-driven-Analysis-for-iNverse-fft-Yield-Evaluation  

# kanye v4.6  

## Overview  
**kanye v4.6** is a **Python GUI program** that performs the following operations with an image (actual photo + Inverse FFT image):  

1. Binarizes the Inverse FFT image using a threshold to extract specific regions (pixels).  
2. Classifies the regions using DBSCAN clustering.  
3. Computes the Concave Hull (alpha shape) and calculates the area of each classified cluster.  
4. Overlays the calculation results on the actual image and exports them as a CSV file.  

---

## Key Features and Workflow  

1. **Image Loading**  
   - **Load Real Image Button**  
     - Loads the real (original) image and saves the path in the global variable `real_image_path`.  
   - **Load Inverse FFT Image Button**  
     - Loads the Inverse FFT image and saves the path in the global variable `inverse_fft_image_path`.  

2. **Parameter Settings**  
   - **Threshold (Slider)**: Range 0–255  
     - Used for binarizing (thresholding) the Inverse FFT image.  
   - **eps (Slider)**: DBSCAN parameter (range 0–20, step 0.1).  
   - **min_samples (Slider)**: DBSCAN parameter (range 1–100).  
   - **alpha (Slider)**: Alpha shape (`alphashape`) parameter (range 0.01–1.0, step 0.01).  
   - **Default values**: Threshold: 45, eps: 11.0, min_samples: 30, alpha: 0.2.  
   - **1_pixel_area + Unit (Combobox)**  
     - Physical area per pixel.  
     - Units: `nm²` or `µm²`.  
   - **Min Cluster Size**  
     - When drawing the alpha shape, clusters with fewer points than this value are ignored.  
   - **Show Cluster IDs (Checkbutton)**  
     - Whether to display labels (IDs) at the center of each cluster.  

3. **Apply Button**  
   - Uses the set parameters to display a Matplotlib Figure overlaying the real image.  
   - Displays the area of each cluster and the “Total Area” in the left Listbox.  

4. **Export Image**  
   - Saves the overlaid result image as PNG/JPG, etc.  

5. **Export CSV**  
   - Exports each cluster's ID and area to a CSV file.  

---

## Installation and Execution  

1. **Install Required Libraries**  
   ```bash
   pip install Pillow opencv-python numpy matplotlib scikit-learn alphashape shapely
   ```

2. **Packaging**  
   ```bash
   pip install pyinstaller
   pyinstaller --onefile kanye_v4_6.py
   pyinstaller --onefile area_calculator.py
   ```

