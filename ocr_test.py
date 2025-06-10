import cv2
import pytesseract
import numpy as np
import re
from pdf2image import convert_from_path
from textblob import TextBlob

def clean_text(text):
    text = text.replace("\n", " ").strip()  
    text = re.sub(r"[^a-zA-Z0-9.,'\"?!:;()\[\]\s]", "", text)  
    text = re.sub(r"\s+", " ", text)  
    return text

pdf_path = "test.pdf"
#dpi = 300
min_area = 300
line_gap_thresh = 30
expand_margin = 1000  

pages = convert_from_path(pdf_path, 300)

for page_num, page in enumerate(pages, 1):
    image = np.array(page)
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

    mask = cv2.inRange(hsv, (10, 40, 150), (180, 255, 255))
    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) > min_area]
    boxes = sorted(boxes, key=lambda b: (b[1], b[0]))  

    line_groups = []
    for box in boxes:
        x, y, w, h = box
        if not line_groups:
            line_groups.append([[x, y, x+w, y+h]])
        else:
            last_group = line_groups[-1]
            _, last_y, _, last_y2 = last_group[0]
            if abs(y - last_y) < line_gap_thresh:
                line_groups[-1].append([x, y, x+w, y+h])
            else:
                line_groups.append([[x, y, x+w, y+h]])

    highlighted_texts = []

    for group in line_groups:
        if len(group) > 1:
            x1 = min(g[0] for g in group)
            y1 = min(g[1] for g in group)
            x2 = max(g[2] for g in group)
            y2 = max(g[3] for g in group)

            x1 = max(x1 - expand_margin, 0)
            x2 = min(x2 + expand_margin, image.shape[1])

            roi = image[y1:y2, x1:x2]
            text = pytesseract.image_to_string(roi)
            if text.strip():
                cleaned = clean_text(text)
                corrected = str(TextBlob(cleaned).correct())
                highlighted_texts.append(corrected)


        else:
            x1, y1, x2, y2 = group[0]
            roi = image[y1:y2, x1:x2]
            text = pytesseract.image_to_string(roi)
            if text.strip():
                cleaned = clean_text(text)
                corrected = str(TextBlob(cleaned).correct())
                highlighted_texts.append(corrected)


    if highlighted_texts:
        print(f"\n Page {page_num} Highlighted Text:")
        for i, txt in enumerate(highlighted_texts, 1):
            print(f"{i}. {txt}")
    else:
        print(f"\n Page {page_num}: No highlighted text found.")
