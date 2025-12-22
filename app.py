from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os
import requests



app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret")

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY",)
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY",)



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

            print("Выбрана функция:", function)
            print("Период:", period)

            # позже здесь будет обработка

            image_filename = session.get("image_filename")

    else:
        image_filename = session.get("image_filename")

    return render_template(
        'upload.html',
        image_filename=image_filename
    )




@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)