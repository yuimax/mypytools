# myftp.py

import ftplib
import os
import re
import ssl
import enum
import fnmatch
import pathlib

from datetime import datetime, timezone
from collections import namedtuple
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

# FTPサーバー情報
ServerInfo = namedtuple('ServerInfo', ['host', 'port', 'user', 'passwd', 'root'])

_my_servers = {
    'my-ftp-server' : ServerInfo('ftp.example.net', 21,   'user', 'pass', '/htdocs/'),
    'local-ftp'     : ServerInfo('localhost',       2121, 'aaa',  'aaa',  '/pub/'),
}


# リモート側のみ存在するファイルの扱い
class RemoteOnlyOp(enum.Enum):
    KEEP = enum.auto()       # なにもせず残す
    DOWNLOAD = enum.auto()   # ローカル側にダウンロード
    DELETE = enum.auto()     # リモート側を削除


# 有効なFTPサーバー名のリストを得る
def get_server_names():
    return list(_my_servers.keys())


# 指定した名前のFTPサーバーの情報を得る
def get_server_info(name):
    if name in _my_servers:
        return _my_servers[name]
    else:
        server_names = get_server_names()
        raise Exception(f"ERROR: myftp.get_server_info('{name}'): not in {server_names}")


# 指定した名前のFTPサーバーにログインする
#   戻り値として、ftplib.FTP または ftplib.FTP_TLS のオブジェクトに、
#   ServerInfo 型の server_info プロパティを追加したものを返す
def login(server_name):
    server_info = get_server_info(server_name)
    (host, port, user, passwd, root) = server_info
    try:
        if re.search(r'fc2\.com', host):
            # fc2 はTLSログインできないので ftplib.FPS クラスを使う
            # 平文でパスワードを送るのでセキュリティ的に問題あり
            ftp = ftplib.FTP()
        elif re.search(r'xrea\.com', host):
            # xrea はTLSログイン可能だがセキュリティレベルを1に下げないとエラーになる
            my_context = ssl.create_default_context()
            my_context.set_ciphers('DEFAULT@SECLEVEL=1')
            ftp = ftplib.FTP_TLS(context=my_context)
        else:
            # 上記以外（sakura と lolipop）はTLSログイン可能
            ftp = ftplib.FTP_TLS()
        ftp.server_info = server_info
        ftp.connect(host, port)
        ftp.login(user, passwd)
        return ftp
    except Exception as ex:
        raise Exception(f"ERROR: myftp.login(): {ex}")


# FTPサーバーの指定したディレクトリに移動する
# remote_pathやその途中のディレクトリがなければ作成する
def cwd(ftp, remote_path):
    path = '/'
    for d in [d for d in remote_path.split('/') if d]:
        path = os.path.join(path, d).replace(os.sep, '/')
        try:
            # cwdに成功すればディレクトリは存在する
            ftp.cwd(path)
        except ftplib.error_perm:
            # ディレクトリが存在しない場合、作成してからcwdする
            ftp.mkd(path)
            ftp.cwd(path)
            print(f"create: remote {path}")


# FTPタイム文字列をタイムスタンプに変換する
def timestr_to_timestamp(ftp_timestr):
    dt_naive = datetime.strptime(ftp_timestr, "%Y%m%d%H%M%S")
    dt_utc = dt_naive.replace(tzinfo=timezone.utc)
    return dt_utc.timestamp()


# タイムスタンプをFTPタイム文字列に変換する
def timestamp_to_timestr(local_timestamp):
    dt_utc = datetime.fromtimestamp(local_timestamp, tz=timezone.utc)
    return dt_utc.strftime('%Y%m%d%H%M%S')


# ローカルファイルのタイムスタンプを取得しFTPタイム文字列に変換する
def get_timestr(local_path):
    timestamp = os.path.getmtime(local_path)
    return timestamp_to_timestr(timestamp)


# ファイルをアップロードし、タイムスタンプをローカルに合わせる
def upload(ftp, local_path, ftp_path):
    try:
        # リモートディレクトリがなければ作る
        ftp_dir = os.path.dirname(ftp_path)
        cwd(ftp, ftp_dir)

        # バイナリモードでファイルをアップロード
        with open(local_path, 'rb') as f:
            ftp.storbinary(f"STOR {ftp_path}", f)

        # ローカルファイルの最終更新日時を取得
        mfmt_timestr = get_timestr(local_path)

    except Exception as ex:
        raise Exception(f"ERROR: myftp.upload({ftp.host}, {local_path}, {ftp_path}): {ex}")

    try:
        # MFMTコマンドでFTP側のタイムスタンプを設定する
        resp = ftp.sendcmd(f'MFMT {mfmt_timestr} {ftp_path}')
        if resp.startswith('213'): # 通常、成功すると213が返される
            print(f"Upload: {local_path} -> {ftp_path}")
        else:
            print(f"CAUTION: MFMTコマンド失敗: {resp}")

    except ftplib.all_errors as e:
        print(f"CAUTION: MFMTコマンドが利用できません: {e}")


# ファイルをダウンロードし、タイムスタンプをFTP側に合わせる
def download(ftp, local_path, ftp_path):

    try:
        # MDTMコマンドでFTP側のタイムスタンプを得る
        resp = ftp.sendcmd(f'MDTM {ftp_path}')
        if resp.startswith('213'):
            timestr = resp[4:].strip() # "213 " の部分を除去
            local_timestamp = timestr_to_timestamp(timestr)
        else:
            print(f"CAUTION: MDTMコマンド失敗: {resp}")
            local_timestamp = None # 取得失敗の場合はNone

    except ftplib.all_errors as e:
        print(f"CAUTION: MDTMコマンドが利用できません: {e}")
        local_timestamp = None

    # ダウンロードし、タイムスタンプを設定する
    try:
        # ローカルディレクトリがなければ作る
        local_dir = os.path.dirname(local_path)
        if not os.path.exists(local_dir):
            print(f"makedirs: {local_dir}")
            os.makedirs(local_dir)

        # バイナリモードでファイルをダウンロード
        with open(local_path, "wb") as f:
            ftp.retrbinary(f"RETR {ftp_path}", f.write)

        # タイムスタンプを設定
        if local_timestamp is not None:
            os.utime(local_path, (local_timestamp, local_timestamp))

        print(f"Download: {ftp_path} -> {local_path}")

    except Exception as ex:
        raise Exception(f"ERROR: myftp.download({ftp.host}, {local_path}, {ftp_path}): {ex}")


# ファイルリストのソートキー
def custom_sort_key(s):
    has_slash = '/' in s
    return (has_slash, s)


# 複数のファイルをアップロードする
def upload_files(ftp, dirs, files, title):
    if len(files):
        print(title)
        files.sort(key=custom_sort_key)
        for file in files:
            local_path = dirs['local'] + '/' +  file
            ftp_path = dirs['ftp'] + '/' + file
            upload(ftp, local_path, ftp_path)


# 複数のファイルをダウンロードする 
def download_files(ftp, dirs, files, title):
    if len(files):
        print(title)
        files.sort(key=custom_sort_key)
        for file in files:
            local_path = dirs['local'] + '/' +  file
            ftp_path = dirs['ftp'] + '/' + file
            download(ftp, local_path, ftp_path)


# 複数のリモートファイルを削除する
def delete_remote_files(ftp, dirs, files, title):
    if len(files):
        print(title)
        files.sort(key=custom_sort_key)
        try:
            for file in files:
                ftp_path = dirs['ftp'] + '/' + file
                ftp.delete(ftp_path)
                print(f"deleted {ftp_path}")
        except Exception as e:
            print(f"エラー: {e}")


# ファイル名を表示する
def show_files(ftp, dirs, files, title):
    if len(files):
        list.sort(key=custom_sort_key)
        print(title)
        for file in files:
            print(file)

# ファイル数を表示する
def show_count(ftp, dirs, files, title):
    if len(files):
        print(title)
        print(len(files), "same files")


# 辞書srcと辞書dstのキーを比較し、5種類に分類する
def compare_keys(src, dst):
    # 各辞書のキーのsetを作る
    src_keys = set(src.keys())
    dst_keys = set(dst.keys())

    src_only = list(src_keys - dst_keys)    # 1. 辞書srcだけにあるキー
    dst_only = list(dst_keys - src_keys)    # 2. 辞書dstだけにあるキー
    src_old = []    # 3. src[key] < dst[key] であるキー
    src_same = []   # 4. src[key] == dst[key] であるキー
    src_new = []    # 5. src[key] > dst[key] であるキー

    for key in (src_keys & dst_keys): # 両方にあるキー
        if src[key] < dst[key]:
            src_old.append(key)
        elif src[key] == dst[key]:
            src_same.append(key)
        else:
            src_new.append(key)

    return {
        'src_only' : src_only,  # 1. 辞書srcだけにあるキー
        'dst_only' : dst_only,  # 2. 辞書dstだけにあるキー
        'src_old'  : src_old,   # 3. src[key] < dst[key] であるキー
        'src_same' : src_same,  # 4. src[key] == dst[key] であるキー
        'src_new'  : src_new,   # 5. src[key] > dst[key] であるキー
        }


# リモートのファイル一覧を返す
def get_remote_file_list(ftp, ftp_dir, ignore_patterns):
    print('----- scanning remote files')
    result = {}

    def traverse_ftp(current_path):
        try:
            for name, facts in ftp.mlsd(current_path):
                if name == '.' or name == '..':
                    continue
                full_path = os.path.join(current_path, name).replace(os.sep, '/')
                rel_path = os.path.relpath(full_path, ftp_dir).replace(os.sep, '/')
                if is_ignored(rel_path, ignore_patterns):
                    print('ignore:', rel_path)
                else:
                    if facts['type'] == 'dir':
                        traverse_ftp(full_path)
                    elif facts['type'] == 'file':
                        result[rel_path] = facts['modify']
                        # print('  remote:', rel_path)
        except ftplib.error_perm as e:
            # アクセス権がないディレクトリなどはスキップ
            print(f"警告: {current_path}: {e}")
        except Exception as e:
            print(f"エラー: {current_path}: {e}")
            raise

    try:
        cwd(ftp, ftp_dir)
        traverse_ftp(ftp_dir)
    except Exception as e:
        print(f"FTPエラー: {e}")
        raise
    
    print(f"{len(result)} remote files")
    return result


# ローカルのファイル一覧を返す
def get_local_file_list(local_dir, ignore_patterns):
    print('----- scanning local files')

    result = {}
    for root, _, files in os.walk(local_dir):
        for file in files:
            # ローカルディレクトリからの相対パスを取得
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path, local_dir).replace(os.sep, '/')
            # ignoreファイルは無視
            if is_ignored(rel_path, ignore_patterns):
                print('ignore:', rel_path)
            else:
                result[rel_path] = get_timestr(path)
                # print('  local:', rel_path)

    print(f"{len(result)} local files")
    return result


# 複数のignoreファイルの全行をリストとして返す
def load_ignore_list(files):
    print("----- loading ignore files")
    result = []

    for file in files:
        try:
            with open(file, "r") as f:
                for line in f:
                    if s := line.strip():
                        result.append(s)
                print(f"loaded {file}")
        except FileNotFoundError:
            continue
        except Exception:
            raise

    result = list(set(result))
    print(f"{len(result)} ignore patterns")
    for i, pat in enumerate(result):
        print(f"#{i+1} [{pat}]")
    return result


# 指定されたファイルが除外対象か確認
def is_ignored(filename, ignore_patterns):
    return any(fnmatch.fnmatch(filename, pattern) for pattern in ignore_patterns)


# ローカルとFTPサーバーのディレクトリを同期する
def mirror(local_dir, server_name, remote_only_op):
    with login(server_name) as ftp:
        # ローカルとFTPのディレクトリ
        dirs = {
            'local': local_dir,
            'ftp': os.path.join(ftp.server_info.root, local_dir).replace(os.sep, '/'),
        }

        # .ftpignore ファイルを読み込む
        home_dir = str(pathlib.Path.home()).replace('\\', '/')
        common_ignore = home_dir + '/myapp/ftp-mirror/.ftpignore'
        local_ignore = dirs['local'] + '/.ftpignore'
        ignore_patterns = load_ignore_list([common_ignore, local_ignore])

        # ローカルのファイルの一覧（パスと更新時刻）を得る
        local_files = get_local_file_list(dirs['local'], ignore_patterns)

        # リモートのファイル一覧（パスと更新時刻）を得る
        remote_files = get_remote_file_list(ftp, dirs['ftp'], ignore_patterns)

        # ローカルとリモートの情報を比較して5種類に分類する
        files = compare_keys(local_files, remote_files)

        show_count(ftp, dirs, files['src_same'], '----- check same')
        upload_files(ftp, dirs, files['src_new'] + files['src_only'], '----- upload')
        download_files(ftp, dirs, files['src_old'], '----- download')

        # remote_only_op で処理方法を帰る
        match remote_only_op:
            case RemoteOnlyOp.KEEP:
                show_files(ftp, dirs, files['dst_only'], '----- keep remmote only')
            case RemoteOnlyOp.DOWNLOAD:
                download_files(ftp, dirs, files['dst_only'], '----- download remote only')
            case RemoteOnlyOp.DELETE:
                delete_remote_files(ftp, dirs, files['dst_only'], '----- delete remmote only')