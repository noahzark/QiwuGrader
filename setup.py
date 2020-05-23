# -*- coding:utf-8 -*-
from setuptools import setup, find_packages
from qiwugrader.app import GRADER_VERSION

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    # ------以下为必需参数
    # 模块名
    name='QiwuGrader',
    # 当前版本
    version=GRADER_VERSION,
    # 简短描述
    description='Qiwu auto test tool, supports accuracy/pressure tests for knowledge base, QA API and server backend',
    # 单文件模块写法
    #py_modules=["qiwugrader"],
    # 多文件模块写法
    packages=find_packages(),

    # ------以下均为可选参数
    # README
    long_description=long_description,
    long_description_content_type="text/markdown; charset=UTF-8; variant=GFM",
    # 主页链接
    url='https://github.com/noahzark/QiwuGrader',
    # 作者名
    author='noahzark',
    # 作者邮箱
    author_email='lfzh1993@gmail.com',
    classifiers=[
        # 当前开发进度等级（测试版，正式版等）
        'Development Status :: 5 - Production/Stable',

        # 模块适用人群
        'Intended Audience :: Developers',
        # 给模块加话题标签
        'Topic :: Software Development :: Testing',

        # 模块的license
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        # 模块支持的Python版本
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    # 模块的关键词，使用空格分割
    keywords='qiwu qiwugrader',
    # 依赖模块
    install_requires=['requests', 'pyyaml', 'enum34', 'xlrd', 'gevent'],
    # 分组依赖模块，可使用pip install sampleproject[dev] 安装分组内的依赖
    extras_require={
        'srt': ['srt'],
        'pyqt5': ['pyqt5'],
    },
    # 类似package_data, 但指定不在当前包目录下的文件
    # data_files=[('my_data', ['data/data_file'])],
    # 新建终端命令并链接到模块函数
    entry_points={'console_scripts': [
        'qiwugrader = qiwugrader:main',
        'qiwugrader.compare = qiwugrader:compare',
        'qiwugrader.generate = qiwugrader:generate',
    ]},
    # 项目相关的额外链接
    project_urls={
        'Bug Reports': 'https://github.com/noahzark/QiwuGrader/issues',
        'Say Thanks!': 'https://qiwu.ai',
        'Source': 'https://github.com/noahzark/QiwuGrader',
    },
)
