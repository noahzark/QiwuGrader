# coding=utf8
from enum import Enum
import re
import string
import random
import pprint


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
