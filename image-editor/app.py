from flask import Flask, request, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import os
import requests

app = Flask(__name__)

def wrap_text(text, font, max_width, draw):
    lines = []
    words = text.split()
    line = ''
    for word in words:
        test_line = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return '\n'.join(lines)

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
    
    text = request.form.get('text', 'Default Text').replace('"', '').replace("'", '')
    font_size = int(request.form.get('font_size', 40))
    font_color = request.form.get('font_color', 'black')
    position = request.form.get('position', 'center').lower()
    font_style_input = request.form.get('font_style', 'DejaVuSans.ttf')
    background_color = request.form.get('background_color', None)

    draw = ImageDraw.Draw(img)
    
    # Construire le chemin de la police
    font_dir = '/app/fonts/'
    font_style = os.path.join(font_dir, font_style_input) if not font_style_input.startswith(font_dir) else font_style_input

    # Charger la police (utiliser une police par défaut ou téléchargée)
    try:
        font = ImageFont.truetype(font_style, font_size)
    except:
        font = ImageFont.load_default()

    # Calculer la taille du texte avec textbbox
    img_width, img_height = img.size
    wrapped_text = wrap_text(text, font, img_width - 180, draw)
    line_count = wrapped_text.count('\n') + 1
    bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=4)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

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
        margin = 20  # Marge autour du texte
        rradius=10
        sspacing=10
        box_x = x - margin
        box_y = y - margin
        box_width = text_width + 2 * margin
        box_height = text_height + 2 * margin + margin + (sspacing*(line_count-1))
        # Gérer la couleur avec transparence
        try:
            if background_color.startswith('#') and len(background_color) in [7, 9]:
                # Supprimer le # et convertir en valeurs RGB ou RGBA
                color = background_color.lstrip('#')
                if len(color) == 6:  # RGB
                    r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
                    fill_color = (r, g, b, 255)
                else:  # RGBA
                    r, g, b, a = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16), int(color[6:8], 16)
                    fill_color = (r, g, b, a)
            else:
                # Utiliser la couleur telle quelle (nom de couleur ou autre)
                fill_color = background_color
            # Créer une image temporaire pour le cadre avec transparence
            frame_img = Image.new('RGBA', img.size, (0, 0, 0, 0))  # Fond transparent
            frame_draw = ImageDraw.Draw(frame_img)
            frame_draw.rounded_rectangle(
                (box_x, box_y, box_x + box_width, box_y + box_height),
                radius=rradius,  # Rayon pour les coins arrondis
                fill=fill_color
            )
            # Composer l'image principale avec le cadre
            img = Image.alpha_composite(img, frame_img)
            draw = ImageDraw.Draw(img)  # Mettre à jour draw pour le texte
        except Exception as e:
            print(f"Erreur avec background_color {background_color}: {e}")
            frame_draw.rectangle(
                (box_x, box_y, box_x + box_width, box_y + box_height),
                fill='gray'
            )
            img = Image.alpha_composite(img, frame_img)
            draw = ImageDraw.Draw(img)

    # Ajouter le texte
    draw.multiline_text((x, y), wrapped_text, fill=font_color, font=font, spacing=sspacing, align="center")


    # Sauvegarder l'image en mémoire
    output = io.BytesIO()
    img.save(output, format='PNG')
    output.seek(0)

    return send_file(output, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)