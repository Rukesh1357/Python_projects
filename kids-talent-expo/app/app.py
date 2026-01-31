from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/gallery")
def gallery():
    talents = [
        {"kid": "Aarav", "name": "Drawing", "image": "drawing.jpg"},
        {"kid": "Ananya", "name": "Singing", "image": "singing.jpg"},
        {"kid": "Karthik", "name": "Dance", "image": "dance.jpg"},
        {"kid": "Meera", "name": "Sports", "image": "sports.jpg"},
    ]
    return render_template("gallery.html", talents=talents)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

