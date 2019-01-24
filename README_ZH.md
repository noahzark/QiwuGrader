# QiwuGrader
齐悟自动测试工具，支持对 `知识库 / QA问答对 / 服务器后端` 进行 `正确性 / 压力` 测试。

[TOC]

## 作者

Feliciano Long

Zhiyu.Zhou

[统计数据](https://github.com/noahzark/QiwuGrader/graphs/contributors)

## 支持

Python2 > 2.7 及 Python3

## 安装

### 下载源代码

1. Windows用户请先安装（Mac用户可跳过此步）：

https://www.python.org/ftp/python/2.7.15/python-2.7.15.msi

2. （可选步骤）如果系统环境变量没有被正确是设置（无法直接通过cmd/terminal运行python/pip），把python可执行文件及pip路径添加进系统环境变量中 [详情](http://www.runoob.com/python/python-install.html)

3. 安装依赖

``` bash
pip install -r requirements.txt
```

### 下载发行版

[直接下载发行版exe](https://github.com/noahzark/QiwuGrader/releases)

## 使用方法

python app.py `测试用例` `会话数` `会话启动时间`

后两个参数可省略

### 单会话测试

测试一个用例：

``` bash
python app.py ./testcases/test1.yml
```

轮流测试多个用例：

``` bash
python app.py ./testcases/test1.yml ./testcases/test2.yml
```

### 多线程压力测试

使用多个线程进行高并发测试，多线程模式下只会使用一个CPU

5秒内启动10个线程：

``` bash
python app.py ./testcases/test3.yml 10 5
```

在多线程测试中，建议关闭 `print_conversation` 开关以获得更佳的测试报告阅读效果

### 多进程压力测试

使用多个进程进行高并发测试，多进程模式下会启动 **逻辑CPU** 个进程进行测试（每个进程分配 `会话数整除CPU数量`  个任务）。

与多线程类似，当需要测试的 **会话数多于 1000** 且 **启动间隔小于 0.1s** 时，会自动启用多进程模式进行测试。

60s 内进行 1200 次测试：

``` bash
python app.py ./testcases/test4.yml 1200 60
```

## 配置

所有参考的配置样例都在 `testcases` 文件夹下

知识库测试参考 `test1` （带有详细解释的完整测试样例） 和 `test2` （最简测试样例）。 API/模糊匹配测试参照 `test3` （json请求，即QA问答对测试）和 `test4` （表单请求，即知识库后端）

## Windows控制台出现乱码

先输入 `chcp 65001` 激活UTF-8代码页
