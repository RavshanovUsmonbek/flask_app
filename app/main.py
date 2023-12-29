from flask import Flask
from config import DevConfig


app = Flask(__name__)
app.config.from_object(DevConfig)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)