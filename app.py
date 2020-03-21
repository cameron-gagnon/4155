#!/usr/bin/env python3

from app import app

# visit 127.0.0.1:8080/users and 127.0.0.1:8080/user/stroopC to see the magic
app.run(debug=True, host='127.0.0.1', port=8080)
