# QiwuGrader
qiwu auto test tool

## Author

Feliciano Long

## Supports

Python2 > 2.7 and Python3

## Installation

1. For Windows users please download (Mac users could skip this step)

https://www.python.org/ftp/python/2.7/python-2.7.msi

2. Install requirements

``` bash
pip install -r requirements.txt
```

## Usage

single session test

``` bash
python app.py ./testcases/test1.yml
```

multiple session test (start 10 session in 5 seconds)

``` bash
python app.py ./testcases/test3.yml 10 5
```

`print_conversation` switch is suggested to turn off in multiple session test to make report more readable

## Configuration

Examples are under `/testcases` folder

Check `test1` (full explanation) and `test2` (minimum test case) for knowledge tests, `test3` (json request / QA dialogue) and `test4` (form request / knowledge backend) for api test