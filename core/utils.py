import fitz  

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
