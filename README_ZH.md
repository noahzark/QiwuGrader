# QiwuGrader
齐悟自动测试工具

## 作者

Feliciano Long

## 支持

Python2 > 2.7 及 Python3

## 安装

1. Windows用户请先安装（Mac用户可跳过此步）：

https://www.python.org/ftp/python/2.7/python-2.7.msi

2. 安装依赖

``` bash
pip install -r requirements.txt
```

## 使用方法

单会话测试

``` bash
python app.py ./testcases/test1.yml
```

多线程压力测试（5秒内启动10个线程）

``` bash
python app.py ./testcases/test3.yml 10 5
```

在多线程测试中，建议关闭 `print_conversation` 开关以获得更佳的测试报告阅读效果

## 配置

所有参考的配置样例都在 `testcases` 文件夹下
知识库测试参考 `test1` （带有详细解释的完整测试样例） 和 `test2` （最简测试样例）。 API/模糊匹配测试参照 `test3` （json请求，即QA问答对测试）和 `test4` （表单请求，即知识库后端）
