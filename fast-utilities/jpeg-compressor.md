# jpeg compressor in python
## install opencv
```bash
pip install opencv-python
```
## compressor.py
```python
import os
import glob
import cv2

jpeg_quality = 75

current_directory = os.getcwd()
pattern = "*.jpg"
files_list = glob.glob(os.path.join(current_directory, pattern))

for file_name in files_list:
    file_size = os.path.getsize(file_name)
    file_size_kb = file_size / 1024.0
    if file_size_kb > 3000:
        print(f"File: {file_name}, Dimensioni: {file_size_kb:.2f} KB -> processing...")
        img = cv2.imread(file_name)
        cv2.imwrite("d:\\compressed\\"+os.path.basename(file_name), img, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
```
