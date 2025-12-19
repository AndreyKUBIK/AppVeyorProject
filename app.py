from flask import Flask, render_template, request, redirect, url_for, session
import os
import requests



app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret")

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY",)
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY",)
print(bool(os.environ.get("RECAPTCHA_SITE_KEY")))
print(bool(os.environ.get("RECAPTCHA_SECRET_KEY")))

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
    
    if request.method == 'POST':

        if 'image' not in request.files:
            return "Нет файла", 400
        
        image = request.files['image']

        if image.filename == '':
            return "Нет выбранного файла", 400
        
        file_path = os.path.join(UPLOAD_FOLDER, image.filename)
        image.save(file_path)
        return f"Файл {image.filename} успешно загружен"
    return render_template('upload.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)