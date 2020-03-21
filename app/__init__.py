from flask import Flask
from app.controllers import blueprints

app = Flask(__name__, template_folder='../templates')

for blueprint in blueprints:
    app.register_blueprint(blueprint)
