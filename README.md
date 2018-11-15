# Toubans! Discord version
## これって何?
[Toubans!](http://toubans.com)は、西村惟作成の、LINEで動くボットです。開発チームは彼に許可を取ったうえで、Discordへの移植を進めてきました。

チームメンバー:
 * apple502j ソースコードの大半を書いています。
 * kenny2github 通知部分の担当。
 * 西村惟 原作者。

ライセンスは[原作のリポジトリ](https://github.com/nisshi79/line-liff-starter)と同じ、MITライセンスです。

## とりあえずやってみたい人
[Botを招待しましょう。](https://discordapp.com/api/oauth2/authorize?client_id=503480356750753794&permissions=268659776&scope=bot)

以下の権限が必要です:
 * Manage Roles - 設定変更用にRoleを作成します。
 * Manage Messages - 将来当番通知のpinを検討中です。
 * Send Messages - あたりまえ
 * Mention Everyone - 通知文で使えるように

以下はおまけです。ただし**今後使う可能性あり。**
 * Add Reactions
 * Embed Links
 * Read Message History

## Botを所有したい!

1. このrepoをクローンする
```sh
git clone https://github.com/ToubansDiscord/ToubansDiscord.git
```

2. DiscordのBotアカウントを取得する

3. `toubans_token.txt`を作り、トークンを入れる

4. 以下をインストール:

 * Python 3.6.x(それ以外では動かない可能性大)
 * discord.py **rewrite**
 * dateutil (python-dateutil)
 * emoji

注意: aiohttp/discord.pyを使っている場合は、作業前にアンインストールが必要かもしれません。

```sh
pip3 uninstall aiohttp discord
git clone --branch rewrite --depth 1 https://github.com/Rapptz/discord.py.git
cd discord.py
python3 setup.py install
pip3 install python-dateutil emoji
```

5. 実行

```sh
python3 Toubans.py
```

## Discordチャンネルは
[Toubans! Channel](https://discord.gg/yNkNadX)があります。なお、無断でkick/banを行う可能性があるので注意してください。
