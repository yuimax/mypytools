# 質問「柊ゲオルク氏の ppmParse.cpp を Python にコンバートしてください」
# 回答 (Google Gemini)

import os
import shutil
import pathlib
import struct
from typing import Optional, List, Dict, Any

# ==============================================================================
# 補助関数: Search (ディレクトリ探索)
# C++のSearch関数をPathlibと再帰で代替
# ==============================================================================
def search_file(search_folder: str, search_file_lower: str) -> Optional[str]:
    """
    指定フォルダ以下を再帰的に探索し、指定ファイル名（小文字）と一致するファイルのフルパスを返す。
    
    :param search_folder: 探索を開始するフォルダパス。
    :param search_file_lower: 探索対象のファイル名（小文字）。
    :return: 見つかったファイルのフルパス (str)、見つからなかった場合は None。
    """
    try:
        # pathlib.Pathオブジェクトを使用
        start_path = pathlib.Path(search_folder)
        
        # フォルダが存在しない場合は終了
        if not start_path.is_dir():
            return None

        # 再帰的にファイルを探索
        for entry in start_path.rglob('*'):
            if entry.is_file() and entry.name.lower() == search_file_lower:
                return str(entry.resolve()) # 絶対パスを返す
            # C++コードではディレクトリ内のファイルをチェックしてから再帰に入っているが、
            # rglob('*') がファイルとディレクトリを返してくれるため、この処理で代替可能。

    except Exception as e:
        # 権限エラーなどが発生した場合のログ出力 (Python版での代替)
        print(f"Error during file search in {search_folder}: {e}")
        return None
        
    return None

# ==============================================================================
# メイン関数: pmmParse
# C++のpmmParse関数をPythonで代替
# ==============================================================================
def pmm_parse(
    read_file: str,
    out_folder: Optional[str],
    search_folder1: Optional[str],
    search_folder2: Optional[str]
) -> tuple[int, str]:
    """
    PMMファイルを解析し、内部パスを探索フォルダに基づいて書き換え、新しいファイルとして出力する。

    C++のpnmParse関数を再現。Edit関連の処理は標準出力とログリストに置き換える。
    PathListは戻り値の一部として含める。

    :param read_file: 入力PMMファイルのパス。
    :param out_folder: 出力先フォルダのパス。Noneの場合は書き換え・出力を行わない。
    :param search_folder1: 探索フォルダ1。
    :param search_folder2: 探索フォルダ2。
    :return: (結果コード (0: 成功, -1: 失敗), パスリスト (str))
    """
    
    LOGS = [] # EditBufferの代替
    path_list_result: List[str] = [] # PathListの代替

    def log(message: str):
        """ログ出力の代替 (C++のSetWindowText/wsprintfの代替)"""
        LOGS.append(message)
        print(message, end='') # 標準出力にも出す (適宜調整)

    # ----------------------------------------------------------------------
    # ファイル名抽出と拡張子チェック
    # ----------------------------------------------------------------------
    read_path = pathlib.Path(read_file)
    file_name = read_path.name
    
    if not read_path.is_file():
        log(f"エラー: ファイルが見つかりません: {read_file}\r\n")
        return -1, ""
    
    # ファイル名から拡張子をチェック
    try:
        # PMMファイルかチェック（拡張子が大文字・小文字を区別せず 'pmm' か）
        extension = read_path.suffix.lstrip('.').lower()
        
        if not extension:
            log(f"フォルダ{read_file}をパスします。\r\n") # 拡張子がない場合はフォルダ扱い
            return -1, ""
        elif extension != "pmm":
            log(f"ファイル{read_file}をパスします。\r\n")
            return -1, ""
    except:
        log(f"ファイル{read_file}をパスします。\r\n")
        return -1, ""

    # ----------------------------------------------------------------------
    # 出力フォルダの準備
    # ----------------------------------------------------------------------
    out_file = None
    if out_folder:
        if not pathlib.Path(out_folder).is_dir():
            try:
                os.makedirs(out_folder)
            except OSError:
                log("出力フォルダが生成できません。\r\n")
                return -1, ""
        
        out_file = pathlib.Path(out_folder) / file_name

    # ----------------------------------------------------------------------
    # 解析開始ログ
    # ----------------------------------------------------------------------
    log(f"ファイル{read_file}を解析開始しました。\r\n")

    # ----------------------------------------------------------------------
    # 重複対策 (workingファイルへのコピー)
    # ----------------------------------------------------------------------
    current_read_file = read_file
    temp_working_file = None
    if out_folder:
        # C++コードの「重複対策」を再現
        temp_working_file = pathlib.Path(out_folder) / "working.pmm"
        try:
            shutil.copy2(read_file, temp_working_file)
            current_read_file = str(temp_working_file)
        except Exception as e:
            log(f"working.pmmへのコピーに失敗しました: {e}\r\n")
            return -1, ""

    # ----------------------------------------------------------------------
    # PMMファイル解析本体
    # ----------------------------------------------------------------------
    
    # データの構造体をPythonの辞書とリストで代替
    # C++: TCreateData (Path, Data, Count) の連結リスト
    # Python: [{ 'data': bytes, 'path': str }] のリスト
    create_data_list: List[Dict[str, Any]] = []
    
    try:
        # PMMファイルはバイナリモードで処理
        with open(current_read_file, 'rb') as rfp:
            # ファイル全体を読み込む (C++のようにチャンク処理しないことで単純化)
            file_data = rfp.read()
            
            # C++コードは500バイトずつ読んで Before/Main/After のバッファで処理しているが、
            # Pythonでは一度に読み込み、バイト配列として処理する
            data_buffer = bytearray(file_data)
            i = 0 # 現在のインデックス (C++の i に相当)
            start = 0 # 前回の書き換えが発生した位置 (C++の Start に相当)
            
            # C++コードのループ処理を再現
            while i < len(data_buffer):
                # '.' の検出
                if data_buffer[i:i+1] == b'.':
                    j = i + 1
                    
                    # 拡張子の判定 ( Inc の代替。j-2 から 6バイトを読み込む)
                    # C++: memcpy(Inc,Main + j - 2, 6); strlwr(Inc);
                    # Pythonでは、i+1 から始まるファイル名っぽい部分をチェック
                    
                    # 少なくとも 5バイト (.xxx\0) が必要 (i+1 + 3 + 1 = i+5)
                    if j + 3 < len(data_buffer): 
                        inc_bytes = data_buffer[j - 2 : j + 4] # .ext の部分を含む6バイト
                        inc_str_lower = inc_bytes.lower().decode('ascii', errors='ignore')

                        ml = 0
                        # 拡張子チェックのロジックを再現 (ファイル名がフルパス表記かどうかもチェック)
                        
                        # j から遡って ':' (ドライブレターやプロトコル) を探す
                        p = j
                        while p >= 0 and data_buffer[p] != ord(b':'):
                            p -= 1
                        has_full_path = p >= 0 and data_buffer[p] == ord(b':')
                        
                        # --------------------------------
                        # .pmd, .avi, .bmp, .wav のチェック
                        # --------------------------------
                        if (inc_str_lower[2:5] == "pmd" or \
                            inc_str_lower[2:5] == "avi" or \
                            inc_str_lower[2:5] == "bmp" or \
                            inc_str_lower[2:5] == "wav") and has_full_path:
                            
                            i += 4 # .ext (4文字) 分進める
                            ml = 1
                        
                        # --------------------------------
                        # .x のチェック
                        # --------------------------------
                        elif len(inc_str_lower) >= 4 and \
                             inc_str_lower[0] != '\x00' and \
                             inc_str_lower[1] == '.' and \
                             inc_str_lower[2] == 'x' and \
                             inc_str_lower[3] == '\x00' and has_full_path:
                            
                            i += 2 # .x (2文字) 分進める
                            ml = 1

                        # --------------------------------
                        # パス/ファイル名抽出と書き換え処理
                        # --------------------------------
                        if ml == 1:
                            # TargetPath (フルパス部分) と TargetFile (ファイル名部分) を抽出
                            
                            # TargetFileの終端: i (現在は .ext の次)
                            # TargetFileの始端: 'j' から '\\' が見つかるまで遡る (ファイル名)
                            j_file_start = i - 1 # .ext の直前から開始
                            while j_file_start >= 0 and data_buffer[j_file_start] != ord(b'\\'):
                                j_file_start -= 1
                            j_file_start += 1 # ファイル名の開始位置
                            
                            # TargetPathの終端: i-1
                            # TargetPathの始端: 'j' から ':' が見つかるまで遡り、さらに1文字戻す
                            j_path_start = j_file_start - 1
                            while j_path_start >= 0 and data_buffer[j_path_start] != ord(b':'):
                                j_path_start -= 1
                            j_path_start -= 1 # ':' の前の文字（ドライブレターの 'C' など）
                            if j_path_start < 0:
                                j_path_start = 0 # バグ対策
                            
                            # TargetPath (C++の TargetPath)
                            # i - j_path_start の長さで TargetPath を抽出
                            path_bytes = data_buffer[j_path_start : i]
                            target_path = path_bytes.decode('shift_jis', errors='ignore').rstrip('\x00')
                            
                            # TargetFile (C++の TargetFile)
                            # i - j_file_start の長さで TargetFile を抽出
                            file_bytes = data_buffer[j_file_start : i]
                            target_file = file_bytes.decode('shift_jis', errors='ignore').rstrip('\x00')
                            
                            # PathListに追加
                            path_list_result.append(target_path)
                            
                            log("----------------------------------------\r\n")
                            log(f"パス{target_path}を書き換えます。\r\n")
                            
                            # --------------------------------
                            # データ構造体の構築 (書き換え前のデータ保存)
                            # --------------------------------
                            
                            # 1. 前回の書き換えから今回のパスの始端までのデータ (Main[Start]...Main[j-1])
                            # C++: j-Start の長さのデータ
                            data_chunk = data_buffer[start:j_path_start]
                            create_data_list.append({
                                'data': data_chunk,
                                'path': '',
                                'count': len(data_chunk)
                            })
                            
                            # 2. 今回のパス文字列 (書き換え対象) の情報
                            # C++: TargetPath, TargetFile
                            target_file_unicode = target_file.lower()
                            find_path = None
                            
                            # --------------------------------
                            # 探索ロジック
                            # --------------------------------
                            if out_folder:
                                if search_folder1:
                                    find_path = search_file(search_folder1, target_file_unicode)
                                
                                if find_path is None and search_folder2:
                                    find_path = search_file(search_folder2, target_file_unicode)
                            
                            
                            # --------------------------------
                            # パス書き換えの実行
                            # --------------------------------
                            
                            if out_folder and find_path: # 見つかった場合 (書き換え)
                                log(f"パス{find_path}に変更しました。\r\n----------------------------------------\r\n")
                                
                                # 新しいパスを Shift-JIS (CP_ACP) にエンコード
                                new_path_bytes = find_path.encode('shift_jis', errors='ignore')
                                
                                # 元のパス (target_path) と新しいパス (find_path) の長さ比較
                                len_original = len(path_bytes)
                                len_new = len(new_path_bytes)
                                
                                # 3. 新しいパス情報
                                create_data_list.append({
                                    'data': new_path_bytes, # 新しいパスのバイト列
                                    'path': find_path, # ログ用
                                    'count': len_new
                                })
                                
                                # 4. 長さ調整用のパディング (C++のロジック再現)
                                diff = len_original - len_new
                                if diff > 0: # 新しいパスが短い -> ヌル文字でパディング
                                    padding = b'\x00' * diff
                                    create_data_list.append({
                                        'data': padding,
                                        'path': '',
                                        'count': diff
                                    })
                                elif diff < 0: # 新しいパスが長い -> 読み込み位置をずらす
                                    i += -diff # iを巻き戻して次のループで長い部分を処理
                                    # C++ではメインバッファの i の位置にヌル文字を追加しているが、
                                    # Pythonでは i を移動させるだけで対応。
                                
                            
                            elif out_folder and not find_path: # 見つからなかった場合
                                # avi, wav のみ続行可能
                                ext_lower = inc_str_lower[2:5]
                                if ext_lower == "avi" or ext_lower == "wav":
                                    log(f"ファイル{target_file}が見つかりませんでした。続行します。\r\n----------------------------------------\r\n")
                                    # 元のパスをそのまま使用 (そのまま書き出す)
                                    create_data_list.append({
                                        'data': path_bytes,
                                        'path': target_path,
                                        'count': len(path_bytes)
                                    })
                                else:
                                    log(f"ファイル{target_file}が見つかりませんでした。失敗しました。\r\n----------------------------------------\r\n")
                                    return -1, ""

                            
                            # 次の検索開始位置を i に設定 (i は既に .ext の後になっている)
                            start = i
                            i -= 1 # ループの最後で i++ されるため、1つ戻す (C++の --i; //相殺//iの場所が先頭だから。 に相当)

                i += 1
            
            # --------------------------------
            # ファイルの末尾部分のデータをリストに追加
            # --------------------------------
            # C++: CreateDataNow->Count = i - Start; memcpy(CreateDataNow->Data, Main + Start, i - Start);
            data_chunk_end = data_buffer[start:i]
            create_data_list.append({
                'data': data_chunk_end,
                'path': '',
                'count': len(data_chunk_end)
            })

    except FileNotFoundError:
        log(f"エラー: PMMファイルが見つかりません: {current_read_file}\r\n")
        return -1, ""
    except Exception as e:
        log(f"解析中に予期せぬエラーが発生しました: {e}\r\n")
        return -1, ""

    # ----------------------------------------------------------------------
    # ファイル書き出し
    # ----------------------------------------------------------------------
    if out_folder and out_file:
        try:
            with open(out_file, 'wb') as wfp:
                for item in create_data_list:
                    wfp.write(item['data'])
            
            log(f"ファイル{out_file}を出力完了しました。\r\n")
        
        except Exception as e:
            log(f"ファイルの書き出しに失敗しました: {e}\r\n")
            return -1, ""

    # ----------------------------------------------------------------------
    # 後処理 (workingファイルの削除)
    # ----------------------------------------------------------------------
    if temp_working_file and out_folder:
        try:
            os.remove(temp_working_file)
        except OSError as e:
            log(f"working.pmmの削除に失敗しました: {e}\r\n")


    # PathListの文字列化
    path_list_str = ",".join(path_list_result)

    return 0, path_list_str

# ----------------------------------------------------------------------
# 実行例
# ----------------------------------------------------------------------
if __name__ == '__main__':
    # この部分は実行環境に合わせて変更してください
    # 存在しないファイルとフォルダを指定して、動作テストを行ってください。
    
    # テスト用のダミーファイルを作成 (実際にはPMMファイルを準備してください)
    # PMMファイルはバイナリファイルなので、このテストコードは単なる実行例です。
    
    # 仮想的なファイルパス
    DUMMY_READ_FILE = "test_input.pmm"
    DUMMY_OUT_FOLDER = "test_output"
    DUMMY_SEARCH_FOLDER1 = "search_dir_1"
    DUMMY_SEARCH_FOLDER2 = "search_dir_2"
    
    # テストディレクトリのセットアップ
    os.makedirs(DUMMY_SEARCH_FOLDER1, exist_ok=True)
    os.makedirs(DUMMY_SEARCH_FOLDER2, exist_ok=True)
    os.makedirs(DUMMY_OUT_FOLDER, exist_ok=True)
    
    # pmmParse のロジックはバイナリデータ内のパス文字列のバイト操作に大きく依存しているため、
    # 実際のPMMファイルと依存ファイルを準備してテストする必要があります。
    
    # 簡単な実行例
    # result_code, paths = pmm_parse(
    #     read_file=DUMMY_READ_FILE, 
    #     out_folder=DUMMY_OUT_FOLDER,
    #     search_folder1=DUMMY_SEARCH_FOLDER1, 
    #     search_folder2=DUMMY_SEARCH_FOLDER2
    # )
    
    # print(f"\n--- 実行結果 ---")
    # print(f"結果コード: {result_code}")
    # print(f"検出されたパス: {paths}")
    
    # 実行後、生成されたディレクトリを削除したい場合はコメントを外す
    # shutil.rmtree(DUMMY_OUT_FOLDER)
    # shutil.rmtree(DUMMY_SEARCH_FOLDER1)
    # shutil.rmtree(DUMMY_SEARCH_FOLDER2)
    pass
