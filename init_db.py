#!/usr/bin/env python

from frontpage import app, db

with app.app_context():
    db.create_all()
