@echo off
REM pip install wheel

rmdir dist /S /Q

python setup.py check
python setup.py sdist
python setup.py bdist_wheel --universal
