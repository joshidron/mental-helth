from fpdf import FPDF
import os

font_path = os.path.join("static", "fonts", "Nirmala.ttc")

class TestPDF(FPDF):
    def header(self):
        pass

pdf = TestPDF()
pdf.add_page()

if os.path.exists(font_path):
    print(f"Font found at {font_path}")
    try:
        pdf.add_font("Nirmala", style="", fname=font_path)
        pdf.set_font("Nirmala", size=12)
        
        text = "ગુજરાતી"
        width = pdf.get_string_width(text)
        print(f"String width for '{text}': {width}")
        
        if width > 0:
            print("SUCCESS: Font seems to handle the characters (width > 0).")
        else:
            print("FAILURE: Font returned 0 width for characters.")
            
    except Exception as e:
        print(f"Error loading font: {e}")
else:
    print("Font file NOT found.")
