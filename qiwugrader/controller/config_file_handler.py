# -*- coding:utf-8 -*-
import yaml

from qiwugrader.grader.compatible import open_config_file

__author__ = 'Feliciano'


class YamlConfigFileHandler:
    resp_dict = {}

    def __init__(self, filename: str):
        self.filename = filename

        with open_config_file(self.filename) as __fr:
            if hasattr(yaml, 'FullLoader'):
                self.resp_dict = yaml.load(__fr, Loader=yaml.FullLoader)
            else:
                self.resp_dict = yaml.load(__fr)

    def get_config(self, key, default={}):
        return self.resp_dict[key] if key in self.resp_dict else default
