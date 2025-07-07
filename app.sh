#!/bin/bash

alembic upgrade head
export PYTHONPATH=$PYTHONPATH:`pwd`
python3 bot/runbot.py