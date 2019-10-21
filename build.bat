@echo off
pip install wheel

python setup.py sdist
python setup.py bdist_wheel --universal