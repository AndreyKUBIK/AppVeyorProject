import os
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY")
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY")

print("SITE KEY:", bool(RECAPTCHA_SITE_KEY))
print("SECRET KEY:", bool(RECAPTCHA_SECRET_KEY))
@app.route("/")
def index():
    return render_template("index.html", site_key=RECAPTCHA_SITE_KEY)

@app.route("/submit", methods=["POST"])
def submit():
    token = request.form.get("g-recaptcha-response")

    payload = {
        "secret": RECAPTCHA_SECRET_KEY,
        "response": token
    }

    response = requests.post(
        "https://www.google.com/recaptcha/api/siteverify",
        data=payload
    )
    result = response.json()

    if result.get("success"):
        return "Капча пройдена ✅"
    else:
        return "Капча не пройдена ❌"

if __name__ == "__main__":
    app.run()
