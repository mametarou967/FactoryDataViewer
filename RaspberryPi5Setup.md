# RaspberryPi5SetupAndApp

# TODO

* [ ] グラフ化と集計方法
* [ ] パトランプを正しく判定する方法の考察

# IP設定

```
https://qiita.com/mochi_2225/items/15c1e7c1c1ae79f97501
```

# プロキシ設定

```
https://qiita.com/gae-22/items/308f3f375cf0f5b0e5cb
```

# ヘッドレス環境

```
https://zenn.dev/thorie/articles/548emb-raspberry-pi-5-os-setup
```

# ブラウザで全角/半角を切り替えれるようにする

* 以下のコマンドを実行
```
sudo apt update
sudo apt install fcitx5 fcitx5-mozc fcitx5-config-qt fcitx5-frontend-gtk3
nano ~/.xprofile
```

* xprofileに以下の記述を追加
```
export GTK_IM_MODULE=fcitx5
export QT_IM_MODULE=fcitx5
export XMODIFIERS="@im=fcitx5
```

* 再起動
```
sudo reboot
```

* 起動後コンフィグツールを開く
```
fcitx5-configtool
```

* 「Global Config（全体設定）> Trigger Input Method（入力メソッドを切り替えるキー）」で設定
半角全角を押して切り替え


# リモートデスクトップの設定方法

```
https://techblog-ai.com/%E3%80%90raspberry-pi-5%E3%80%91%E3%83%AA%E3%83%A2%E3%83%BC%E3%83%88%E3%83%87%E3%82%B9%E3%82%AF%E3%83%88%E3%83%83%E3%83%97%E6%8E%A5%E7%B6%9A%E6%96%B9%E6%B3%95realvnc/
```


## 起動時の設定

* 有線LANで接続していると起動時に自動的にIPアドレスが割り振られている(自宅の場合は192.168.50.19だった)
* Enable Raspberry Pi Connectを有効にする

## プロキシの設定

* 記入予定

* 確認方法
  * webブラウザに接続できるか確認する

## 起動後のアップデート

## 必要なライブラリのインストール

## 有線LAN設定方法

## リモートデスクトップの設定

## 共有フォルダの設定
