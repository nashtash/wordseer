#!/usr/bin/env python

"""Run the wordseer_flask website.
"""
from app import app

if __name__ == '__main__':
	# TODO: port config for production?
    app.run(host='0.0.0.0')
