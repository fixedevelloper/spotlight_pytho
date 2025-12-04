from flask import Flask, request, jsonify
import pytesseract
from PIL import Image
import os
import time

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Si Tesseract n'est pas dans le PATH (Windows) :
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


@app.route('/ocr', methods=['POST'])
def ocr_endpoint():
    if 'image' not in request.files:
        return jsonify({"success": False, "message": "Aucune image reçue."}), 400

    image_file = request.files['image']
    user_id = request.form.get('user_id')
    type_ocr = request.form.get('type')  # meter_number ou index

    if not user_id or not type_ocr:
        return jsonify({"success": False, "message": "user_id et type sont obligatoires."}), 400

    # Sauvegarder l'image
    filename = f"{int(time.time())}_{image_file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    image_file.save(filepath)

    # Lire et exécuter OCR
    try:
        img = Image.open(filepath)
    
        raw_text = pytesseract.image_to_string(img, lang="eng", config="--psm 6")
    except Exception as e:
        return jsonify({"success": False, "message": "Erreur OCR", "error": str(e)}), 500

    # Extraction ciblée
    meter_number = None
    index_value = None

    # Numéro compteur : 5 à 12 chiffres
    if type_ocr == "meter_number":
        import re
        match = re.search(r"\b\d{5,12}\b", raw_text)
        if match:
            meter_number = match.group(0)

    # Index consommation : 1 à 7 chiffres
    if type_ocr == "index":
        import re
        match = re.search(r"\b\d{1,7}\b", raw_text)
        if match:
            index_value = match.group(0)

    return jsonify({
        "success": True,
        "userId": user_id,
        "type": type_ocr,
        "rawText": raw_text.strip(),
        "meterNumber": meter_number,
        "consumptionIndex": index_value
    })


if __name__ == "__main__":
    app.run(port=5000, debug=True)
