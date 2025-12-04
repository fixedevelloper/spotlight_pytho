#!/bin/bash

# ===========================
# CONFIGURATION
# ===========================
APP_NAME="ocr_service"
APP_DIR="/var/www/$APP_NAME"
USER="www-data"
DOMAIN="ocr.agensic.com"  # changer par ton domaine ou IP
LOCAL_CODE_DIR="./app_code" # dossier local contenant ocr_service.py et preprocess.py
PORT=80

# ===========================
# 1. Vérifier / installer Python3 et pip
# ===========================
if ! command -v python3 &> /dev/null
then
    echo "Python3 non trouvé. Installation..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
fi

# ===========================
# 2. Vérifier / installer Tesseract OCR
# ===========================
if ! command -v tesseract &> /dev/null
then
    echo "Tesseract non trouvé. Installation..."
    sudo apt install -y tesseract-ocr tesseract-ocr-fra
fi

# ===========================
# 3. Installer dépendances système pour OpenCV et Nginx
# ===========================
sudo apt install -y libsm6 libxext6 libxrender-dev nginx ufw

# ===========================
# 4. Créer dossier application
# ===========================
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR
cd $APP_DIR || exit

# ===========================
# 5. Créer environnement virtuel
# ===========================
python3 -m venv venv
source venv/bin/activate

# ===========================
# 6. Installer dépendances Python
# ===========================
pip install --upgrade pip
pip install flask pytesseract pillow opencv-python gunicorn

# ===========================
# 7. Créer dossier uploads
# ===========================
mkdir -p uploads
chmod 777 uploads

# ===========================
# 8. Copier le code dans APP_DIR
# ===========================
if [ ! -d "$LOCAL_CODE_DIR" ]; then
    echo "ERREUR: Le dossier $LOCAL_CODE_DIR n'existe pas. Crée-le avec ocr_service.py et preprocess.py"
    exit 1
fi

cp $LOCAL_CODE_DIR/* $APP_DIR/
echo "✅ Code copié dans $APP_DIR"

# ===========================
# 9. Configurer Nginx
# ===========================
NGINX_CONF="/etc/nginx/sites-available/$APP_NAME"
sudo tee $NGINX_CONF > /dev/null <<EOL
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOL

sudo ln -s $NGINX_CONF /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
echo "✅ Nginx configuré"

# ===========================
# 10. Créer le service systemd
# ===========================
SERVICE_FILE="/etc/systemd/system/$APP_NAME.service"
sudo tee $SERVICE_FILE > /dev/null <<EOL
[Unit]
Description=OCR Service
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 0.0.0.0:8000 ocr_service:app

[Install]
WantedBy=multi-user.target
EOL

sudo systemctl daemon-reload
sudo systemctl enable $APP_NAME
sudo systemctl start $APP_NAME
sudo systemctl status $APP_NAME
echo "✅ Service systemd créé et démarré"

# ===========================
# 11. Configurer UFW pour HTTP
# ===========================
sudo ufw allow 80
sudo ufw enable
sudo ufw status

# ===========================
# 12. FIN
# ===========================
echo "🎉 Déploiement terminé ! Ton microservice OCR est maintenant disponible sur http://$DOMAIN/ocr"
