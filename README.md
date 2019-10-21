# QiwuGrader

Qiwu auto test tool, supports `accuracy / pressure` tests for `knowledge base, QA API and server backend`

[Chinese version](https://github.com/noahzark/QiwuGrader/blob/master/README_ZH.md)

[TOC]

## 1. Author

Feliciano Long

Zhiyu.Zhou

[Statics](https://github.com/noahzark/QiwuGrader/graphs/contributors)

## 2. Supports

Python2 > 2.7 and Python3 (preferred)

## 3. Installation

### Install from PYPI

`pip install QiwuGrader`

### Download source code

1. For Windows users please download (Mac users could skip this step)

https://www.python.org/ftp/python/2.7.15/python-2.7.15.msi

2. (Optional) If Environment Variables is not set correctly, add python executable and pip script to system Path. [How to](https://www.pythoncentral.io/add-python-to-path-python-is-not-recognized-as-an-internal-or-external-command/)

3. Install requirements

``` bash
pip install -r requirements.txt
```

### ~~Download release~~

Deprecated, please install using pip

[~~Release executable~~](https://github.com/noahzark/QiwuGrader/releases)

## 4. Run

last two parameters are ignorable

### Run from module

```bash
qiwugrader [testcase] [session number] [test duration]
```

or

```bash
python -m qiwugrader.app [testcase] [session number] [test duration]
```

### Run from source

```bash
python qiwugrader/app.py [testcase] [session number] [test duration]
```

## 5. Usage

### single session test

test one case:

``` bash
qiwugrader ./testcases/test1.yml
```

test multiple cases:

``` bash
qiwugrader ./testcases/test1.yml ./testcases/test2.yml
```

### multiple session test (multi threading)

Use multiple threads to test, in this mode only one CPU is used.

start 10 sessions in 5 seconds

``` bash
qiwugrader ./testcases/test3.yml 10 5
```

`print_conversation` switch is suggested to turn off in multiple session test to make report more readable

### multiple session test (multi processing)

Use multiple processes to test, in this mode the program will start **logical CPU number** processes (each assigned `session number DIV CPU number` tasks)

Similar to multi threading test, this mode will be enabled when **session count larget than 1000** and **start interval less than  0.1s**

start 1200 sessions in 60 seconds

``` bash
qiwugrader ./testcases/test4.yml 1200 60
```

## 6. Configuration

Examples are under `/testcases` folder

Check `test1` (full explanation) and `test2` (minimum test case) for knowledge tests, `test3` (json request / QA dialogue) and `test4` (form request / knowledge backend) for api test
