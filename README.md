# masK-driven-Analysis-for-iNverse-fft-Yield-Evaluation

# kanye v4.6

## 개요
**kanye v4.6**은 이미지(실제 사진 + Inverse FFT 이미지)를 불러와서,  
1. Inverse FFT 이미지를 임계값(Threshold)으로 이진화하여 특정 영역(픽셀)을 추출  
2. DBSCAN 클러스터링을 통해 영역을 분류  
3. 분류된 영역(클러스터)에 대한 Concave Hull(알파 셰이프)을 구해 넓이를 계산  
4. 계산 결과를 실제 이미지 위에 오버레이(overlay)한 후, CSV로 내보내기

등의 작업을 수행하는 **파이썬 GUI 프로그램**입니다.

---

## 주요 기능 및 흐름

1. **이미지 로드**  
   - **Load Real Image 버튼**  
     - 실제(원본) 이미지를 불러오고, 전역 변수 `real_image_path`에 저장  
   - **Load Inverse FFT Image 버튼**  
     - Inverse FFT 이미지를 불러오고, 전역 변수 `inverse_fft_image_path`에 저장  

2. **파라미터 설정**  
   - **Threshold (슬라이더)**: 0–255 범위  
     - Inverse FFT 이미지를 이진화(Thresholding)할 때 사용  
   - **eps (슬라이더)**: DBSCAN 파라미터 (0–20, 0.1 단위)  
   - **min_samples (슬라이더)**: DBSCAN 파라미터 (1–100)  
   - **alpha (슬라이더)**: 알파 셰이프(`alphashape`) 파라미터 (0.01–1.0, 0.01 단위)
   - 기본값: **Threshold: 45, eps: 11.0, min_samples: 30, alpha: 0.2**
   - **1_pixel_area + 단위(Combobox)**  
     - 1픽셀당 물리적 면적  
     - 단위: `nm²`, `µm²` 중 선택 가능   
   - **Min Cluster Size**  
     - 알파 셰이프를 그릴 때 클러스터 내부 포인트가 이 값보다 작으면 무시  
   - **Show Cluster IDs (Checkbutton)**  
     - 각 클러스터 중심에 라벨(ID) 표시 여부

3. **Apply 버튼**  
   - 설정된 파라미터를 이용하여 실제 이미지를 오버레이한 결과를 Matplotlib Figure로 표시  
   - 각 클러스터 넓이와 “Total Area”를 왼쪽 Listbox에 표시

4. **Export Image**  
   - 오버레이된 결과 이미지를 PNG/JPG 등으로 저장

5. **Export CSV**  
   - 각 클러스터의 ID와 넓이를 CSV로 내보냄

---

## 설치 및 실행

1. **필수 라이브러리 설치**  
   ```bash
   pip install Pillow opencv-python numpy matplotlib scikit-learn alphashape shapely

2. **패키징**
    ```bash
    pip install pyinstaller
    pyinstaller --onefile kanye_v4_6.py
    pyinstaller --onefile area_calculator.py

3. **exe 다운로드**
   - [kanye v4.6 실행 파일 다운로드](https://drive.google.com/drive/folders/17UrETzXa2XQx_Zxlp6kS1Rvkj8ptRYmB?usp=share_link)
