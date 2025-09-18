# myutil.py

import os
import pathlib


# HOMEディレクトリを得る
def get_home_dir():
    return str(pathlib.Path.home()).replace(os.sep, '/')


# 相対パスを得る
def get_rel_path(full_path, base_dir):
    return os.path.relpath(full_path, base_dir).replace(os.sep, '/')


# パスを結合する
def join_path(parent, child):
    return os.path.join(parent, child).replace(os.sep, '/')
