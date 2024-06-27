#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# python 入口函数
if __name__ == '__main__':
    #  批量修改文件名称
    import os
    import re
    import sys
    import json
    import copy
    import requests

    # 获取当前目录下的所有文件
    files = os.listdir(os.getcwd())
    # 遍历所有文件
    for file in files:
        # 匹配文件名
        match = re.match(r'(.*)\.(\d+)', file)
        if match:
            # 获取文件名
            name = match.group(1)
            # 获取文件后缀
            suffix = match.group(2)
            # 文件重命名
            os.rename(file, name + '.txt')
            print('文件重命名成功: ' + file + ' -> ' + name + '.txt')
        else:
            print('文件名不匹配: ' + file)