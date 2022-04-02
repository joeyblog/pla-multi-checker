# PLA MMO Checker
大大大発生の個体を検索します。

# 使い方

0 box1を空にする。

1 村でセーブ

2 大発生へ行き、最初の4匹に同時バトルし、全て捕獲

2-a 逃げるポケモンの場合… 煙玉+餌でスポーンポイントから少し離れたところに4匹集めて、ボールで捕獲

3 残りも全て捕まえる

4 最初の群れの数を数える（8 or 9 or 10）

5 後続の数も数える(6 or 7)

6 村へ戻り、交換のところへ

7 botに$dumpと送信

8 最初の1匹目から、順にホバーしていく

9 botから受け取った.pa8ファイルをmoフォルダーへ

10 EtumrepMMO.ConsoleApp.exeを実行してseed特定


逃げるポケモンの場合、Show Default Paths Only✔で
1匹ずつスポーンさせるパターンのみ表示

# 記号の解説
（例）
First Round Path: [1, 1, 3] + Revisit [3, 2] + Bonus Path: 2

First Round Path: [1, 1, 3]→最初の群れで、1匹、1匹、3匹同時に捕獲/倒す

Revisit [3, 2]→残り3体になったときに120m以上離れたところにテレポート/移動して、戻って1匹捕獲。
残り2体になったときにも120m以上離れたところにテレポート/移動して、戻って残りを捕獲

Bonus Path: 2→後続の群れで、2匹同時捕獲/倒す

Bonus Init Spawn X→後続の群れの最初のX匹目のポケモンとして出現


# 逃げるポケモンかどうか（同時に複数匹の戦闘が可能かどうか）
https://shinyhunter.club/tools/arceus-available-pokemon-mmo

## 必要なもの
* [Python](https://www.python.org/downloads/)
* [Nintendo Switch Online](https://www.nintendo.co.jp/hardware/switch/onlineservice/pricing/index.html)

## Credits:
* Cappy for original one
