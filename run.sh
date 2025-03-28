#!/bin/bash
export FLASK_APP=app.py
export FLASK_ENV=development
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 -m flask run
