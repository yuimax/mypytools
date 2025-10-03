# pip install scipy.io

import numpy as np
from scipy.io import wavfile
import argparse
import os
import sys

# フレームレートの定義（1/30秒フレームの場合）
FRAME_RATE_FOR_OPTION = 30 

def add_silence_to_wav(input_filepath, output_filepath, length, unit):
    """
    WAVファイルの先頭に指定した長さの無音部分を挿入し、新しいファイルとして保存する。

    :param input_filepath: 入力WAVファイルのパス
    :param output_filepath: 出力WAVファイルのパス
    :param length: 無音部分の長さ（単位によってミリ秒またはフレーム）
    :param unit: 長さの単位 ('ms' または 'frame')
    :raises FileNotFoundError: 入力ファイルが存在しない場合
    :raises Exception: WAVファイルの読み書きエラーなど
    """
    
    if not os.path.exists(input_filepath):
        raise FileNotFoundError(f"エラー: 入力ファイルが見つかりません: {input_filepath}")

    print(f"入力ファイル: {input_filepath}")
    
    try:
        # WAVファイルの読み込み
        # rate: サンプリングレート (Hz)
        # data: 音声データ (NumPy配列)
        rate, data = wavfile.read(input_filepath)
    except Exception as e:
        raise Exception(f"エラー: WAVファイルの読み込みに失敗しました: {e}")

    # サンプル数（データポイント数）を計算
    if unit == 'ms':
        # ミリ秒 (ms) からサンプル数を計算: rate (サンプル/秒) * length (ms) / 1000 (ms/秒)
        silence_samples = int(rate * length / 1000)
        print(f"無音の長さ: {length} ミリ秒 -> {silence_samples} サンプル")
    elif unit == 'frame':
        # フレーム (1/30秒) からサンプル数を計算: rate (サンプル/秒) * length (フレーム) / FRAME_RATE_FOR_OPTION (フレーム/秒)
        silence_samples = int(rate * length / FRAME_RATE_FOR_OPTION)
        print(f"無音の長さ: {length} フレーム (1/{FRAME_RATE_FOR_OPTION}秒) -> {silence_samples} サンプル")
    else:
        # このエラーはargparseで防がれるが、念のため
        raise ValueError(f"エラー: 不正な単位 '{unit}' が指定されました。'ms' または 'frame' を使用してください。")

    if silence_samples <= 0:
        print("警告: 指定された長さが無効またはゼロです。処理をスキップします。")
        # 元ファイルをコピーする処理なども考えられるが、ここでは単に終了とする
        return

    # データタイプ (dtype) とチャンネル数を取得
    dtype = data.dtype
    if data.ndim == 1:
        # モノラル
        channels = 1
        # 無音データを生成 (dtypeを合わせることが重要)
        silence_data = np.zeros(silence_samples, dtype=dtype)
    else:
        # ステレオまたはマルチチャンネル
        channels = data.shape[1]
        # 無音データを生成 (形状を (サンプル数, チャンネル数) に合わせる)
        silence_data = np.zeros((silence_samples, channels), dtype=dtype)

    # 無音データと元の音声データを結合
    new_data = np.concatenate((silence_data, data))

    try:
        # 新しいWAVファイルとして保存
        wavfile.write(output_filepath, rate, new_data)
        print(f"成功: 無音を挿入したファイルを保存しました: {output_filepath}")
    except Exception as e:
        raise Exception(f"エラー: WAVファイルの書き出しに失敗しました: {e}")


if __name__ == '__main__':
    # 引数パーサーの設定
    parser = argparse.ArgumentParser(
        description="WAVファイルの先頭に指定した長さの無音部分を挿入するCLI。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # 必須引数
    parser.add_argument(
        'input_file',
        type=str,
        help="入力WAVファイルのパス（例: input.wav）"
    )
    parser.add_argument(
        'output_file',
        type=str,
        help="出力WAVファイルのパス（例: output.wav）"
    )
    
    # 無音の長さを指定するグループ（--ms または --frame のどちらか必須）
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--ms',
        type=int,
        help="無音の長さをミリ秒単位で指定 (例: --ms 500)"
    )
    group.add_argument(
        '--frame',
        type=int,
        help=f"無音の長さをフレーム単位 (1/{FRAME_RATE_FOR_OPTION}秒) で指定 (例: --frame 15)"
    )

    args = parser.parse_args()

    # 単位と長さを決定
    if args.ms is not None:
        length = args.ms
        unit = 'ms'
    elif args.frame is not None:
        length = args.frame
        unit = 'frame'
    else:
        # mutually_exclusive_group で制御されるため通常ここには来ない
        sys.exit("エラー: 無音の長さ(--msまたは--frame)を指定してください。")
        
    try:
        add_silence_to_wav(args.input_file, args.output_file, length, unit)
    except (FileNotFoundError, ValueError, Exception) as e:
        print(e, file=sys.stderr)
        sys.exit(1)
