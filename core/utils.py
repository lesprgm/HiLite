import fitz  
import cv2
import pytesseract
import numpy as np
import re
from pdf2image import convert_from_bytes
#from textblob import TextBlob
from io import BytesIO

from google.cloud import vision

def extract_highlights(file_obj):
    doc = fitz.open(stream=file_obj.read(), filetype="pdf")
    highlights = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"\n--- Page {page_num + 1} ---")
        print("Text on page:", page.get_text())

        annot = page.first_annot

        if not annot:
            print("No annotations on this page.")
        else:
            while annot:
                print("Found annotation type:", annot.type)
                if annot.type[0] == 8:
                    print("Found highlight on page", page_num + 1)
                    words = page.get_text("words")
                    quad_points = annot.vertices
                    sentences = []

                    for i in range(0, len(quad_points), 4):
                        rect = fitz.Quad(quad_points[i:i+4]).rect
                        sentence = " ".join(
                            w[4] for w in words if fitz.Rect(w[:4]).intersects(rect)
                        )
                        sentences.append(sentence)

                    highlights.append(" ".join(sentences))
                annot = annot.next

    return highlights

def clean_text(text):
    text = text.replace("\n", " ").strip()  
    text = re.sub(r"[^a-zA-Z0-9.,'\"?!:;()\[\]\s]", "", text)  
    text = re.sub(r"\s+", " ", text)  
    return text

def extract_highlights_or_fallback(file_obj):
    file_bytes = file_obj.read()

    highlights = extract_highlights(BytesIO(file_bytes))
    if highlights:
        return highlights
    
    client = vision.ImageAnnotatorClient()

    highlighted_texts = []
    pages = convert_from_bytes(file_bytes, 150)

    min_area = 300
    line_gap_thresh = 30
    expand_margin = 300

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
                line_groups.append([[x, y, x + w, y + h]])
            else:
                last_group = line_groups[-1]
                _, last_y, _, last_y2 = last_group[0]
                if abs(y - last_y) < line_gap_thresh:
                    line_groups[-1].append([x, y, x + w, y + h])
                else:
                    line_groups.append([[x, y, x + w, y + h]])

        for group in line_groups:
            if len(group) > 1:
                x1 = min(g[0] for g in group)
                y1 = min(g[1] for g in group)
                x2 = max(g[2] for g in group)
                y2 = max(g[3] for g in group)
                x1 = max(x1 - expand_margin, 0)
                x2 = min(x2 + expand_margin, image.shape[1])
                roi = image[y1:y2, x1:x2]
            else:
                x1, y1, x2, y2 = group[0]
                roi = image[y1:y2, x1:x2]

            '''
            text = pytesseract.image_to_string(roi)
            if text.strip():
                cleaned = clean_text(text)
                corrected = str(TextBlob(cleaned).correct())
                highlighted_texts.append(corrected)
                '''
                
            success, encoded_image = cv2.imencode('.png', roi)
            if not success:
                continue
            content = encoded_image.tobytes()
            gcp_vision_image = vision.Image(content=content)
            
            response = client.document_text_detection(image=gcp_vision_image)
            text = response.full_text_annotation.text
                        
            if text.strip():
                cleaned = clean_text(text)
                
                #corrected = str(TextBlob(cleaned).correct())
                corrected = cleaned
                highlighted_texts.append(corrected)

    return highlighted_texts
