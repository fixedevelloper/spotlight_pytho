import cv2
import numpy as np
from PIL import Image

def preprocess_image(input_path, output_path):
    # Charger l’image
    img = cv2.imread(input_path)

    # Convertir en gris
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Réduction du bruit
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Augmenter contraste (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrast = clahe.apply(denoised)

    # Binarisation adaptative
    thresh = cv2.adaptiveThreshold(
        contrast, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 2
    )

    # Détecter l’inclinaison et corriger
    coords = np.column_stack(np.where(thresh > 0))
    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = thresh.shape
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    deskew = cv2.warpAffine(thresh, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    # Crop automatique pour isoler le texte
    contours, _ = cv2.findContours(deskew, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
        crop = deskew[y:y+h, x:x+w]
    else:
        crop = deskew

    # Sauvegarder résultat
    cv2.imwrite(output_path, crop)

    return output_path
