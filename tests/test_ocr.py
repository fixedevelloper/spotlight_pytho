from PIL import Image
import pytesseract

def test_sample_image():
    img = Image.new('RGB', (100, 30), color = (73, 109, 137))
    text = pytesseract.image_to_string(img)
    assert text is not None
