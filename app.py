from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os
import requests
from PIL import Image
import numpy as np
import math
import matplotlib
matplotlib.use("Agg")  
import matplotlib.pyplot as plt


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret")

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY",)
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY",)

def process_image(input_path, output_path, func, period):
    img = Image.open(input_path).convert("RGB")
    arr = np.array(img).astype(np.float32)

    height, width, _ = arr.shape

    for x in range(width):
        if func == "sin":
            factor = (1 + math.sin(2 * math.pi * x / period)) / 2
        else:
            factor = (1 + math.cos(2 * math.pi * x / period)) / 2

        arr[:, x, :] *= factor

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    Image.fromarray(arr).save(output_path)



def histogram(image_path, output_path, title):
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)

    plt.figure(figsize=(6, 4))

    colors = ['red', 'green', 'blue']
    for i, color in enumerate(colors):
        channel = arr[:, :, i].flatten()
        plt.hist(
            channel,
            bins=256,
            range=(0, 255),
            color=color,
            alpha=0.5,
            label=color.upper()
        )

    plt.title(title)
    plt.xlabel("Яркость")
    plt.ylabel("Количество пикселей")
    plt.legend()
    plt.tight_layout()

    plt.savefig(output_path)
    plt.close()



@app.route('/', methods=['GET', 'POST'])
def CAPTCHA():

    if request.method == 'POST':
        recaptcha_response = request.form.get("g-recaptcha-response")

        if not recaptcha_response:
            return "Капча не пройдена", 400
        
        verify_url = "https://www.google.com/recaptcha/api/siteverify"
        payload = {
            'secret': RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        response = requests.post(verify_url, data=payload)
        result = response.json()

        if result.get("success"):
            session["captcha_passed"] = True
            return redirect(url_for('upload'))
        
        return "Капча не пройдена", 400
    
    return render_template('CAPTCHA.html', site_key=RECAPTCHA_SITE_KEY)



@app.route('/upload', methods=['GET', 'POST'])
def upload():

    if not session.get("captcha_passed"):
        return redirect(url_for('CAPTCHA'))

    image_filename = None
    rocessed_image = None
    original_hist = None
    processed_hist = None

    if request.method == 'POST':

        if 'image' in request.files:

            image = request.files['image']

            if image.filename == '':
                return "Нет выбранного файла", 400

            image_filename = image.filename
            file_path = os.path.join(UPLOAD_FOLDER, image_filename)
            image.save(file_path)

            session["image_filename"] = image_filename

        elif 'function' in request.form:

            function = request.form.get("function")
            period = int(request.form.get("period"))

            image_filename = session.get("image_filename")
            input_path = os.path.join(UPLOAD_FOLDER, image_filename)

            processed_filename = f"processed_{image_filename}"
            output_path = os.path.join(UPLOAD_FOLDER, processed_filename)

            process_image(
                input_path=input_path,
                output_path=output_path,
                func=function,
                period=period
            )

            original_hist = f"hist_original_{image_filename}.png"
            processed_hist = f"hist_processed_{image_filename}.png"

            histogram(
                image_path=input_path,
                output_path=os.path.join(UPLOAD_FOLDER, original_hist),
                title="Гистограмма оригинального изображения"
            )

            histogram(
                image_path=output_path,
                output_path=os.path.join(UPLOAD_FOLDER, processed_hist),
                title="Гистограмма обработанного изображения"
            )

        session["original_hist"] = original_hist
        session["processed_hist"] = processed_hist
        session["processed_image"] = processed_filename

    processed_image = session.get("processed_image")

    return render_template(
        'upload.html',
        image_filename=image_filename,
        processed_image=processed_image,
        original_hist=session.get("original_hist"),
        processed_hist=session.get("processed_hist")
    )



@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)