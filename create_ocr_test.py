from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image(text, output_path):
    # Create a white image
    img = Image.new('RGB', (400, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # Try to use a default font
    try:
        font = ImageFont.load_default()
    except:
        font = None
        
    d.text((10, 10), text, fill=(0, 0, 0), font=font)
    img.save(output_path)
    print(f"Test image created at: {output_path}")

if __name__ == "__main__":
    create_test_image("OCR TEST: The quick brown fox jumps over the lazy dog.", "uploads/ocr_test.png")
