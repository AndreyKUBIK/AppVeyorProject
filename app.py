from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os
import requests
from PIL import Image
import numpy as np
import math


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
            period = request.form.get("period")

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

            session["processed_image"] = processed_filename

    processed_image = session.get("processed_image")

    return render_template(
        'upload.html',
        image_filename=image_filename,
        processed_image=processed_image
    )



@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)