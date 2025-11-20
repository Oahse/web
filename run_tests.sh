#!/bin/bash
source backend/.venv/bin/activate
python backend/init_db.py
PYTHONPATH=backend pytest backend/tests