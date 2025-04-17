from flask import Flask
from routes import app as routes_app

app = routes_app
app.secret_key = "1111"

if __name__ == "__main__":
    app.run(debug=True)
