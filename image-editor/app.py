from flask import Flask, request, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import os
import requests

app = Flask(__name__)

@app.route('/add-text', methods=['POST'])
def add_text():
    # Vérifier si un lien d'image est fourni
    image_url = request.form.get('image_url')
    if not image_url:
        return {"error": "No image URL provided"}, 400
    
    # Télécharger l'image depuis le lien
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content)).convert('RGBA')
    except Exception as e:
        return {"error": f"Failed to load image: {str(e)}"}, 400
    
    text = request.form.get('text', 'Default Text')
    font_size = int(request.form.get('font_size', 40))
    font_color = request.form.get('font_color', 'black')
    position = request.form.get('position', 'center').lower()
    font_style = request.form.get('font_style', 'arial.ttf')
    background_color = request.form.get('background_color', None)

    draw = ImageDraw.Draw(img)

    # Charger la police (utiliser une police par défaut ou téléchargée)
    try:
        font = ImageFont.truetype(font_style, font_size)
    except:
        font = ImageFont.load_default()

    # Calculer la taille du texte avec textbbox
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    img_width, img_height = img.size

    if position == 'center':
        x = (img_width - text_width) // 2
        y = (img_height - text_height) // 2
    elif position == 'top':
        x = (img_width - text_width) // 2
        y = 10
    elif position == 'bottom':
        x = (img_width - text_width) // 2
        y = img_height - text_height - 10
    else:
        x, y = 10, 10

    # Appliquer un fond si spécifié
    if background_color:
        # Créer une image de fond
        bg_img = Image.new('RGBA', img.size, background_color)
        bg_img.paste(img, (0, 0), img)
        img = bg_img
        draw = ImageDraw.Draw(img)

    # Ajouter le texte
    draw.text((x, y), text, fill=font_color, font=font)

    # Sauvegarder l'image en mémoire
    output = io.BytesIO()
    img.save(output, format='PNG')
    output.seek(0)

    return send_file(output, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)