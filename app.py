from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Import Flask-Migrate
 

app = Flask(__name__)




import config

# Configure the app from config
app.config.from_object(config.Config) 

# Initialize SQLAlchemy (don't pass the app here, we'll do it in models.py)
db = SQLAlchemy(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

import models

import api

import routes




if __name__ == '__main__ ':
    app.run(debug=True) 