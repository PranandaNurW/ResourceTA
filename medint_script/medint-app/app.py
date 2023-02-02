from flask import Flask, render_template
from be import get_trend_data

app = Flask(__name__)

@app.route("/")
def index():
    data = get_trend_data()[:9]
    return render_template("index.html", data=data)

if __name__ == "__main__":
    app.run(port=5000)