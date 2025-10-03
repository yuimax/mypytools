# mypytools
* 自作 Python スクリプト保管庫

## 内容
* [bin](bin)/ -- 実行ファイル用フォルダ： 環境変数 PATH に登録しておく
* [lib](lib)/ -- モジュール用フォルダ： 環境変数 PYTHONPATH に登録しておく
* [test](test)/ -- テスト用のバッチファイルなど

|bin/コマンド|説明|備考|
|:---|:---|:---|
|[bom.py](bin/bom.py)|UTF-8ファイルのBOMを処理する|BOMのチェック、除去、付加|
|[ftp-server.py](bin/ftp-server.py)|ローカルFTPサーバー|FTP関連プログラムの動作テスト用|
|[image-info.py](bin/image-info.py)|画像情報|画像の 形式,幅,高さ を表示する|
|[ksan.py](bin/ksan.py)|簡易計算機|入力をeval()で評価し表示するだけ|
|[urldecode.py](bin/urldecode.py)|URLデコーダー|URLエンコード文字列をデコードする|
|[video-info.py](bin/video-info.py)|動画情報|動画の 幅,高さ,FPS,フレーム数,視聴時間 を表示する|
|[wav-cut.py](bin/wav-cut.py)|音声切り出し|WAVファイルの指定範囲を切り出す|
|[wav-delay.py](bin/wav-delay.py)|音声遅らせ|WAVファイルの先頭に無音を挿入|
|[wipe.py](bin/wipe.py)|指定したファイルを0バイトにする|元のファイルはゴミ箱に移動する|



