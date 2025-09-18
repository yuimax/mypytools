# myftp.py

import collections
import datetime
import enum
import fnmatch
import ftplib
import os
import ssl
import tomllib
from myutil import get_home_dir, join_path, get_rel_path

# リモート側のみ存在するファイルの扱い
class RemoteOnlyOp(enum.Enum):
    KEEP = enum.auto()  # なにもせず残す
    DOWNLOAD = enum.auto()  # ローカル側にダウンロード
    DELETE = enum.auto()  # リモート側を削除


# 個々のFTPサーバーの設定
FtpConfig = collections.namedtuple('FtpConfig', ['host', 'port', 'user', 'passwd', 'root'])


# FTPサーバー情報を設定ファイルから読み出す
def load_config() -> dict[str, FtpConfig]:
    config_file = 'myftp_conf.toml'
    config_path = join_path(os.path.dirname(__file__), config_file)
    with open(config_path, 'rb') as f:
        config_data = tomllib.load(f)
    config_dict = {}
    for nickname, data in config_data.items():
        assert isinstance(data, dict)
        config_dict[nickname] = FtpConfig(**data)
    return config_dict


# FTPサーバー情報を _ftp_configs に格納する
_ftp_configs = load_config()


# 有効なFTPサーバー名のリストを得る
def get_ftp_names():
    return list(_ftp_configs.keys())


# 指定した名前のFTPサーバーの情報を得る
def get_ftp_config(name: str):
    if name in _ftp_configs:
        return _ftp_configs[name]
    else:
        raise Exception(f"ERROR: myftp.get_ftp_config('{name}'): not in {et_ftp_names()}")


# Verboseモード
_is_verbose = False


# Verboseモードの設定
def verbose(flag):
    # メモ：　グローバル変数を変更する場合は global 宣言が必要
    # （global 宣言なしで代入すると関数内ローカル変数が作られる）
    global _is_verbose
    return (_is_verbose := bool(flag))


# Verboseモードを考慮してメッセージを表示する
def vprint(s):
    if _is_verbose:
        print(s)


# 指定した名前のFTPサーバーにログインする
#   戻り値として、ftplib.FTP または ftplib.FTP_TLS のオブジェクトに、
#   FtpConfig 型の ftp_config プロパティを追加したものを返す
def login(server_name):
    ftp_config = get_ftp_config(server_name)
    (host, port, user, passwd, root) = ftp_config
    try:
        if 'fc2.com' in host:
            # fc2 はTLSログインできないので ftplib.FPS クラスを使う
            # 平文でパスワードを送るのでセキュリティ的に問題あり
            ftp = ftplib.FTP()
        elif 'xrea.com' in host:
            # xrea はTLSログイン可能だがセキュリティレベルを1に下げないとエラーになる
            my_context = ssl.create_default_context()
            my_context.set_ciphers('DEFAULT@SECLEVEL=1')
            ftp = ftplib.FTP_TLS(context=my_context)
        else:
            # 上記以外（sakura.ne.jp と lolipop.jp）はTLSログイン可能
            ftp = ftplib.FTP_TLS()
        ftp.ftp_config = ftp_config
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
        path = join_path(path, d)
        try:
            # cwdに成功すればディレクトリは存在する
            ftp.cwd(path)
        except ftplib.error_perm:
            # ディレクトリが存在しない場合、作成してからcwdする
            ftp.mkd(path)
            ftp.cwd(path)
            vprint(f"mkd: {path}")


# FTPタイム文字列をタイムスタンプに変換する
def timestr_to_timestamp(ftp_timestr):
    dt_naive = datetime.datetime.strptime(ftp_timestr, '%Y%m%d%H%M%S')
    dt_utc = dt_naive.replace(tzinfo=datetime.timezone.utc)
    return dt_utc.timestamp()


# タイムスタンプをFTPタイム文字列に変換する
def timestamp_to_timestr(local_timestamp):
    dt_utc = datetime.datetime.fromtimestamp(local_timestamp, tz=datetime.timezone.utc)
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
        with open(local_path, "rb") as f:
            ftp.storbinary(f"STOR {ftp_path}", f)

        # ローカルファイルの最終更新日時を取得
        mfmt_timestr = get_timestr(local_path)

    except Exception as ex:
        raise Exception(f"ERROR: myftp.upload({ftp.host}, {local_path}, {ftp_path}): {ex}")

    try:
        # MFMTコマンドでFTP側のタイムスタンプを設定する
        resp = ftp.sendcmd(f"MFMT {mfmt_timestr} {ftp_path}")
        if resp.startswith('213'):  # 通常、成功すると213が返される
            vprint(f"upload: {local_path} -> {ftp_path}")
        else:
            vprint(f"CAUTION: MFMTコマンド失敗: {resp}")

    except ftplib.all_errors as e:
        print(f"CAUTION: MFMTコマンドが利用できません: {e}")


# ファイルをダウンロードし、タイムスタンプをFTP側に合わせる
def download(ftp, local_path, ftp_path):

    try:
        # MDTMコマンドでFTP側のタイムスタンプを得る
        resp = ftp.sendcmd(f"MDTM {ftp_path}")
        if resp.startswith('213'):
            timestr = resp[4:].strip()  # "213 " の部分を除去
            local_timestamp = timestr_to_timestamp(timestr)
        else:
            print(f"CAUTION: MDTMコマンド失敗: {resp}")
            local_timestamp = None  # 取得失敗の場合はNone

    except ftplib.all_errors as e:
        print(f"CAUTION: MDTMコマンドが利用できません: {e}")
        local_timestamp = None

    # ダウンロードし、タイムスタンプを設定する
    try:
        # ローカルディレクトリがなければ作る
        local_dir = os.path.dirname(local_path)
        if not os.path.exists(local_dir):
            vprint(f"makedirs: {local_dir}")
            os.makedirs(local_dir)

        # バイナリモードでファイルをダウンロード
        with open(local_path, 'wb') as f:
            ftp.retrbinary(f"RETR {ftp_path}", f.write)

        # タイムスタンプを設定
        if local_timestamp is not None:
            os.utime(local_path, (local_timestamp, local_timestamp))

        vprint(f"download: {ftp_path} -> {local_path}")

    except Exception as ex:
        raise Exception(f"ERROR: myftp.download({ftp.host}, {local_path}, {ftp_path}): {ex}")


# ファイルリストのソートキー
def custom_sort_key(s):
    # '/' がないものを優先、それ以外は文字列としてソート
    has_slash = '/' in s
    return (has_slash, s)


# 複数のファイルをアップロードする
def upload_files(ftp, local_dir, files, title):
    if len(files):
        vprint(title)
        files.sort(key=custom_sort_key)
        count = 0
        for file in files:
            local_path = join_path(local_dir, file)
            ftp_path = join_path(ftp.ftp_config.root, local_path)
            upload(ftp, local_path, ftp_path)
            count += 1
        print(f"{count} uploaded")


# 複数のファイルをダウンロードする
def download_files(ftp, local_dir, files, title):
    if len(files):
        vprint(title)
        files.sort(key=custom_sort_key)
        count = 0
        for file in files:
            local_path = join_path(local_dir, file)
            ftp_path = join_path(ftp.ftp_config.root, local_path)
            download(ftp, local_path, ftp_path)
            count += 1
        print(f"{count} downloaded")


# 複数のリモートファイルを削除する
def delete_remote_files(ftp, local_dir, files, title):
    if len(files):
        vprint(title)
        files.sort(key=custom_sort_key)
        count = 0
        try:
            for file in files:
                local_path = join_path(local_dir, file)
                ftp_path = join_path(ftp.ftp_config.root, local_path)
                ftp.delete(ftp_path)
                print(f"delete: {ftp_path}")
        except Exception as e:
            print(f"ERROR: {e}")
        print(f"{count} deleted")


# ファイル名を表示する
def show_files(ftp, files, title):
    if len(files):
        files.sort(key=custom_sort_key)
        vprint(title)
        for file in files:
            print(file)


# ファイル数を表示する
def show_count(ftp, files, title):
    if len(files):
        vprint(title)
        print(len(files), "same files")


# 辞書srcと辞書dstのキーを比較し、5種類に分類する
def compare_keys(src, dst):
    # 各辞書のキーのsetを作る
    src_keys = set(src.keys())
    dst_keys = set(dst.keys())

    src_only = list(src_keys - dst_keys)  # 1. 辞書srcだけにあるキー
    dst_only = list(dst_keys - src_keys)  # 2. 辞書dstだけにあるキー
    src_old = []  # 3. src[key] < dst[key] であるキー
    src_same = []  # 4. src[key] == dst[key] であるキー
    src_new = []  # 5. src[key] > dst[key] であるキー

    for key in src_keys & dst_keys:  # 両方にあるキー
        if src[key] < dst[key]:
            src_old.append(key)
        elif src[key] == dst[key]:
            src_same.append(key)
        else:
            src_new.append(key)

    return {
        "src_only": src_only,  # 1. 辞書srcだけにあるキー
        "dst_only": dst_only,  # 2. 辞書dstだけにあるキー
        "src_old": src_old,  # 3. src[key] < dst[key] であるキー
        "src_same": src_same,  # 4. src[key] == dst[key] であるキー
        "src_new": src_new,  # 5. src[key] > dst[key] であるキー
    }


# リモートのファイル一覧を返す
def get_remote_file_list(ftp, ftp_dir, ignore_patterns):
    vprint("----- scanning remote files")
    result = {}

    def scan_ftp(cur_path):
        try:
            for name, facts in ftp.mlsd(cur_path):
                if name == "." or name == "..":
                    continue
                full_path = join_path(cur_path, name)
                rel_path = get_rel_path(full_path, ftp_dir)
                if is_ignored(rel_path, ignore_patterns):
                    vprint(f"ignore: {rel_path}")
                else:
                    if facts["type"] == "dir":
                        scan_ftp(full_path)
                    elif facts["type"] == "file":
                        result[rel_path] = facts["modify"]
                        vprint(f"remote: {rel_path}")
        except ftplib.error_perm as e:
            # 読めないディレクトリなどはスキップ
            # print(f"CAUTION: {cur_path}: {e}")
            pass

    scan_ftp(ftp_dir)
    print(f"{len(result)} remote files")
    return result


# ローカルのファイル一覧を返す
def get_local_file_list(local_dir, ignore_patterns):
    vprint("----- scanning local files")
    result = {}

    def scan_local(cur_path):
        for name in os.listdir(cur_path):
            if name == "." or name == "..":
                continue
            full_path = join_path(cur_path, name)
            rel_path = get_rel_path(full_path, local_dir)
            if is_ignored(rel_path, ignore_patterns):
                vprint(f"ignore: {rel_path}")
            else:
                if os.path.isdir(full_path):
                    scan_local(full_path)
                elif os.path.isfile(full_path):
                    result[rel_path] = get_timestr(full_path)
                    vprint(f"local: {rel_path}")

    scan_local(local_dir)
    print(f"{len(result)} local files")
    return result


# 複数のignoreファイルの全行をリストとして返す
def load_ignore_list(files):
    vprint("----- loading ignore files")
    result = []

    for file in files:
        try:
            with open(file, "r") as f:
                result += (line.strip() for line in f)
            vprint(f"loaded {file}")
        except FileNotFoundError:
            continue

    result = list(set(result))
    vprint(f"{len(result)} ignore patterns")
    for i, pat in enumerate(result):
        vprint(f"#{i+1} [{pat}]")
    return result


# 指定されたファイルが除外対象か確認
def is_ignored(filename, ignore_patterns):
    return any(fnmatch.fnmatch(filename, pattern) for pattern in ignore_patterns)


# ローカルとFTPサーバーのディレクトリを同期する
def mirror(server_name, local_dir, remote_only_op):
    print(f"{'=' * 40} mirror('{server_name}', '{local_dir}', {remote_only_op})")

    # .ftpignore ファイルを読み込む
    common_ignore = join_path(get_home_dir(), "mypylibs/.ftpignore")
    local_ignore = join_path(local_dir, '.ftpignore')
    ignore_patterns = load_ignore_list([common_ignore, local_ignore])

    with login(server_name) as ftp:
        # ローカルのファイル一覧（パスと更新時刻）を得る
        local_files = get_local_file_list(local_dir, ignore_patterns)

        # リモートのファイル一覧（パスと更新時刻）を得る
        ftp_dir = join_path(ftp.ftp_config.root, local_dir)
        remote_files = get_remote_file_list(ftp, ftp_dir, ignore_patterns)

        # ローカルとリモートの情報を比較して5種類に分類する
        files = compare_keys(local_files, remote_files)

        # 変化していないファイルを表示する
        show_count(ftp, files["src_same"], "----- check same")

        # 双方に存在しローカル側が新しいファイル、FTP側に存在しないファイルをアップロードする
        upload_files(ftp, local_dir, files["src_new"] + files["src_only"], "----- upload")

        # 双方に存在しローカル側が古いファイルをダウンロードする
        download_files(ftp, local_dir, files["src_old"], "----- download")

        # remote_only_op で処理方法を帰る
        match remote_only_op:
            case RemoteOnlyOp.KEEP:
                show_files(ftp, files["dst_only"], "----- keep remmote only")
            case RemoteOnlyOp.DOWNLOAD:
                download_files(ftp, local_dir, files["dst_only"], "----- download remote only")
            case RemoteOnlyOp.DELETE:
                delete_remote_files(ftp, local_dir, files["dst_only"], "----- delete remmote only")

    # 終了メッセージ
    print("done")


# FTPサーバーのディレクトリツリーを全削除する
def rmtree(server_name, target_dir):
    print(f"{'=' * 40} rmtree('{server_name}', '{target_dir}')")

    # FTPのディレクトリを再帰的に削除する
    def rmtree_recursive(cur_path):
        count = 0
        try:
            for name, facts in ftp.mlsd(cur_path):
                if name == "." or name == "..":
                    continue
                child_path = join_path(cur_path, name)
                if facts["type"] == "dir":
                    count += rmtree_recursive(child_path)
                elif facts["type"] == "file":
                    ftp.delete(child_path)
                    count += 1
                    vprint(f"delete: {child_path}")
            ftp.rmd(cur_path)
            vprint(f"rmd: {cur_path}")
        except ftplib.error_perm as e:
            # アクセスできないディレクトリは無視
            print(f"CAUTION: {e}")
        return count

    # FTPサーバーにログインし、ディレクトリツリーを削除する
    with login(server_name) as ftp:
        ftp_dir = join_path(ftp.ftp_config.root, target_dir)
        count = rmtree_recursive(ftp_dir)
        print(f"{count} deleted")

    # 終了メッセージ
    print("done")
