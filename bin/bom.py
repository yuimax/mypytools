# Google Gemini に作ってもらった
#
# そのときの要望と回答：
# https://gist.github.com/yuimax/2c3347c1c6a7aba4764f3b59eadf4689
#
# これをベースに★を記した部分だけ追加した

import argparse
import sys
import glob
import os
from typing import List

# UTF-8のBOM (バイトオーダーマーク): 0xEF, 0xBB, 0xBF
UTF8_BOM = b'\xef\xbb\xbf'

# ★この関数を追加
def cp932_length(s):
    # Shift_JISに変換したときのバイト数を返す
    # コマンドプロンプト画面での文字列の長さと思ってほぼ間違いない
    return len(s.encode('cp932'))


# ★引数に max_arg_length を追加
def check_and_process_file(filepath: str, action: str, max_arg_length: int):
    """
    ファイルをチェックし、指定されたアクション（BOM除去/付加）を実行します。
    """
    try:
        # 1. ファイルを開き、最初の数バイトを読み込んでエンコーディングをチェック
        with open(filepath, 'rb') as f:
            # BOMチェックのため、少なくともBOMのサイズ（3バイト）を読み込む
            initial_bytes = f.read(4096)
            has_bom = initial_bytes.startswith(UTF8_BOM)
            
            # ファイル全体を読み直すためにポインタをリセット
            f.seek(0)
            file_content = f.read()

    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません - {filepath}", file=sys.stdout)
        return
    except IOError as e:
        print(f"エラー: ファイルの読み込みに失敗しました - {filepath} ({e})", file=sys.stdout)
        return

    # 2. UTF-8エンコーディングの確認 (BOMの有無に関わらず)
    # デコードを試みることで、UTF-8として妥当かどうかを確認します
    is_utf8 = False
    try:
        # BOM付き/なしの両方を考慮してデコードを試みる
        file_content.decode('utf-8')
        is_utf8 = True
    except UnicodeDecodeError:
        # UTF-8としてデコードできない場合は、UTF-8ではない
        is_utf8 = False
    
    
    # 3. 結果の表示とアクションの実行
    
    if not is_utf8:
        # UTF-8でない場合
        spaces = ' ' * (max_arg_length - cp932_length(filepath) + 1) #★ spacesを追加
        print(f"{filepath}{spaces}: **UTF-8ではありません**")
        return

    # UTF-8である場合
    bom_status = "BOM付き" if has_bom else "BOMなし"
    spaces = ' ' * (max_arg_length - cp932_length(filepath) + 1) #★ spacesを追加
    print(f"{filepath}{spaces}: UTF-8, {bom_status}")

    # BOM除去オプション (-d)
    if action == 'remove' and has_bom:
        print(f"  -> アクション: BOMを除去します...")
        try:
            # BOMを除去したコンテンツ（BOM付きならBOMサイズ以降）
            new_content = file_content[len(UTF8_BOM):]
            # ファイルに書き戻す
            with open(filepath, 'wb') as f:
                f.write(new_content)
            print("  -> 成功: BOMが除去されました。")
        except IOError as e:
            print(f"  -> エラー: ファイルの書き込みに失敗しました - {e}", file=sys.stdout)
            
    # BOM付加オプション (-a)
    elif action == 'add' and not has_bom:
        print(f"  -> アクション: BOMを付加します...")
        try:
            # BOMを先頭に付加したコンテンツ
            new_content = UTF8_BOM + file_content
            # ファイルに書き戻す
            with open(filepath, 'wb') as f:
                f.write(new_content)
            print("  -> 成功: BOMが付加されました。")
        except IOError as e:
            print(f"  -> エラー: ファイルの書き込みに失敗しました - {e}", file=sys.stdout)
            
    # BOM除去/付加のアクションが指定されたが、対象外の状態だった場合
    elif action in ('remove', 'add'):
        status = "既にBOMがありません。" if action == 'remove' else "既にBOMがあります。"
        print(f"  -> スキップ: {status}")


def main(args: List[str]):
    """
    コマンドライン引数を解析し、メイン処理を実行します。
    """
    parser = argparse.ArgumentParser(
        description="UTF-8ファイルのBOM (バイトオーダーマーク) をチェックし、オプションで除去/付加します。",
        usage='%(prog)s [-d | -a] <file1> [...]'
    )
    
    # 排他的なオプショングループ (削除 -d または追加 -a)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-d', '--remove-bom',
        action='store_true',
        help='指定されたUTF-8ファイルからBOMを除去します。'
    )
    group.add_argument(
        '-a', '--add-bom',
        action='store_true',
        help='指定されたUTF-8ファイルにBOMを付加します。'
    )
    
    # 必須のファイル引数（ワイルドカードを想定）
    parser.add_argument(
        'files',
        nargs='+',  # 1つ以上のファイルパスを受け付ける
        help='処理対象のファイルパス。ワイルドカードが使用可能です (例: "*.txt")。'
    )
    
    # 引数を解析
    parsed_args = parser.parse_args(args)
    
    # 実行するアクションを決定
    action = None
    if parsed_args.remove_bom:
        action = 'remove'
    elif parsed_args.add_bom:
        action = 'add'
    
    # ファイルリストをワイルドカード展開して取得
    all_files = []
    for pattern in parsed_args.files:
        # globを使ってワイルドカードを展開
        matches = glob.glob(pattern)
        # ファイル（ディレクトリではないもの）のみを追加
        all_files.extend([f for f in matches if os.path.isfile(f)])

    if not all_files:
        print("ファイルが見つかりませんでした。", file=sys.stdout)
        # コマンドのヘルプを表示したい場合は、この下を活用できます
        # parser.print_help()
        sys.exit(1)

    max_arg_length = max(cp932_length(path) for path in all_files) #★ max_arg_lengthの取得を追加

    # 各ファイルを処理
    for filepath in all_files:
        check_and_process_file(filepath, action, max_arg_length) #★ 引数にmax_arg_lengthを追加

if __name__ == '__main__':
    # スクリプト名を除いた引数をmain関数に渡す
    main(sys.argv[1:])
