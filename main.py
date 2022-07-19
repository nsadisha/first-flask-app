from flask import Flask

FLASK_ENV=development

app = Flask(__name__)

@app.route("/")
def index():
	print("running")
	return "<h1>Hello world</h1>"