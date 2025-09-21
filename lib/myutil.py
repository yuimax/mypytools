# myutil.py

import os
import pathlib


# HOMEディレクトリを取得し、パス区切り記号を '/' にそろえる
def get_home_dir():
    return str(pathlib.Path.home()).replace(os.sep, '/')


# 相対パスを得て、パス区切り記号を '/' にそろえる
def get_rel_path(full_path, base_dir):
    return os.path.relpath(full_path, base_dir).replace(os.sep, '/')


# パスを結合し、パス区切り記号を '/' にそろえる
def join_path(parent, child):
    return os.path.normpath(os.path.join(parent, child)).replace(os.sep, '/')
