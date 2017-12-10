#!/bin/bash

cd "${0%/*}"
source bin/activate
cd code/
python plane_pal.py
