# pip install numpy scipy

import argparse
import sys
import numpy as np
from scipy.io import wavfile

# 1フレームあたりのミリ秒数 (1/30秒)
FRAME_MS = 1000 / 30

def cut_wav_file_scipy(input_path: str, output_path: str, start: int, end: int, unit: str):
    """
    scipy.io.wavfile を使用してWAVファイルを切り出す関数。
    """
    try:
        # 1. WAVファイルの読み込み
        # rate: サンプリング周波数 (Hz), data: 音声データ (NumPy配列)
        rate, data = wavfile.read(input_path)
    except FileNotFoundError:
        print(f"エラー: 入力ファイルが見つかりません - {input_path}")
        sys.exit(1)
    except Exception as e:
        print(f"エラー: WAVファイルの読み込みに失敗しました - {e}")
        sys.exit(1)

    # 音声データの総サンプル数
    total_samples = len(data)
    # 音声データの長さ (ミリ秒)
    total_ms = int(total_samples / rate * 1000)

    # 2. 範囲の計算 (サンプルインデックスに変換)
    start_sample = 0
    end_sample = total_samples 

    if unit == 'ms':
        # ミリ秒をサンプル数に変換: sample = ms * rate / 1000
        start_sample = int(start * rate / 1000)
        end_sample = int(end * rate / 1000)
    elif unit == 'frame':
        # フレーム数をミリ秒に変換し、それをサンプル数に変換
        start_ms = start * FRAME_MS
        end_ms = end * FRAME_MS
        start_sample = int(start_ms * rate / 1000)
        end_sample = int(end_ms * rate / 1000)
    
    # endが0の場合はファイルの最後までと見なす
    if end == 0 and unit in ('ms', 'frame'):
        end_sample = total_samples

    # 3. 範囲のバリデーション
    if start_sample < 0 or start_sample >= total_samples:
        print(f"エラー: 開始位置が音声ファイルの範囲外です。")
        sys.exit(1)

    if end_sample < start_sample:
        print(f"エラー: 終了位置が開始位置より前です。")
        sys.exit(1)
    
    # 終了位置が総サンプル数を超えている場合は、総サンプル数に丸める
    if end_sample > total_samples:
        end_sample = total_samples
    
    # 4. NumPyのスライス機能で音声データを切り出し
    cut_data = data[start_sample:end_sample]

    # 5. ファイルの書き出し
    try:
        # wavfile.write()でNumPy配列をWAVファイルとして書き込む
        wavfile.write(output_path, rate, cut_data)
        
        print(f"切り出しが完了しました: {output_path}")
        print(f"   サンプリングレート: {rate} Hz")
        print(f"   開始サンプル: {start_sample}, 終了サンプル: {end_sample}")
        print(f"   期間: {(end_sample - start_sample) / rate * 1000:.0f} ms")
    except Exception as e:
        print(f"エラー: ファイルの書き出しに失敗しました - {e}")
        sys.exit(1)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="WAVファイルをミリ秒またはフレーム単位で切り出すツール",
        epilog="例: wav_cutter.py input.wav output.wav -s 1000 -e 5000 -u ms"
    )
    
    # 必須の引数
    parser.add_argument("input_file", help="入力WAVファイルのパス")
    parser.add_argument("output_file", help="出力WAVファイルのパス")

    # 範囲指定の引数
    parser.add_argument("-s", "--start", type=int, required=True,
                        help="切り出しを開始する位置（ミリ秒またはフレーム）")
    parser.add_argument("-e", "--end", type=int, default=0,
                        help="切り出しを終了する位置（ミリ秒またはフレーム）。0の場合はファイルの最後まで。")
    
    # 単位指定の引数
    parser.add_argument("-u", "--unit", choices=['ms', 'frame'], default='ms',
                        help="範囲指定の単位 ('ms': ミリ秒, 'frame': 1/30秒フレーム)。デフォルトは 'ms'")

    args = parser.parse_args()

    # メイン処理の実行
    cut_wav_file_scipy(
        input_path=args.input_file,
        output_path=args.output_file,
        start=args.start,
        end=args.end,
        unit=args.unit
    )
