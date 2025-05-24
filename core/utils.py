import fitz

def extract_highlights(pdf_path):
    doc =fitz.open(pdf_path)
    highlights = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        annot = page.first_annot
        
        while annot:
            if annot.type[0] == 8: #A type 8 annotation is a highlight
                words = page.get_text("words")
                quad_points = annot.vertices
                sentences = []
                
                for i in range(0, len(quad_points), 4):
                    rect = fitz.Quad(quad_points[i:i+4]).rect
                    sentence = " ".join(
                        w[4] for w in words if fitz.Rect(w[:4]).intersects(rect)
                    )
                    sentences.append(sentence)
                    
                highlights.append(" ".join(sentence))
            annot = annot.next
            
        return highlights
            