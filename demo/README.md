---
license: mit
tags:
- object-detection
- computer-vision
- yolov10
datasets:
- detection-datasets/coco
sdk: gradio
sdk_version: 5.0.0b1
---

### Model Description
[YOLOv10: Real-Time End-to-End Object Detection](https://arxiv.org/abs/2405.14458v1)

- arXiv: https://arxiv.org/abs/2405.14458v1
- github: https://github.com/THU-MIG/yolov10

### Installation
```
pip install supervision git+https://github.com/THU-MIG/yolov10.git
```

### Yolov10 Inference
```python
from ultralytics import YOLOv10
import supervision as sv
import cv2

IMAGE_PATH = 'dog.jpeg'

model = YOLOv10.from_pretrained('jameslahm/yolov10{n/s/m/b/l/x}')
model.predict(IMAGE_PATH, show=True)
```

### BibTeX Entry and Citation Info
 ```
@article{wang2024yolov10,
  title={YOLOv10: Real-Time End-to-End Object Detection},
  author={Wang, Ao and Chen, Hui and Liu, Lihao and Chen, Kai and Lin, Zijia and Han, Jungong and Ding, Guiguang},
  journal={arXiv preprint arXiv:2405.14458},
  year={2024}
}
```