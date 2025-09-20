# 画像翻訳ツール

日本語画像を英語に自動翻訳するWindowsデスクトップアプリケーション

## 📁 プロジェクト構成

```
画像翻訳ツール/
├── README.md                 # このファイル
├── requirements.txt          # Python依存パッケージ
├── .env.example             # 環境変数テンプレート
├── .env                     # 環境変数（APIキー設定）
├── .gitignore              # Git除外設定
│
├── config/                  # 設定ファイル
│   └── config.json         # アプリケーション設定
│
├── source/                  # ソースコード
│   ├── main.py             # メインプログラム
│   └── assets/             # 静的リソース
│       └── icons/          # アプリアイコン
│           ├── ON.png      # 自動翻訳ON時アイコン
│           └── OFF.png     # 自動翻訳OFF時アイコン
│
├── images/                 # 翻訳結果画像（自動生成）
├── logs/                   # ログファイル（自動生成）
│
└── docs/                   # ドキュメント
    ├── user_guide.md       # ユーザー利用手順書
    ├── functional_requirements.md  # 機能要件
    └── detailed_design.md  # 詳細設計
```

## 🚀 セットアップ手順

### 1. 依存パッケージのインストール
```bash
pip install -r requirements.txt
```

### 2. APIキーの設定
1. `.env.example`を`.env`にコピー
2. OpenAI APIキーを設定
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. アプリケーション起動
```bash
cd source
python main.py
```

## ⚙️ 設定

アプリケーションの動作は `config/config.json` で調整できます：

- **翻訳品質**: medium ($0.04/枚) または high ($0.17/枚)
- **超精密モード**: アイコンやデザインの変更を防ぐ
- **画像表示設定**: ウィンドウサイズやズーム設定
- **保存設定**: ファイル名フォーマットや保存先

## 📖 詳細情報

- **利用手順**: [docs/user_guide.md](docs/user_guide.md)
- **機能仕様**: [docs/functional_requirements.md](docs/functional_requirements.md)
- **技術仕様**: [docs/detailed_design.md](docs/detailed_design.md)

## 💡 主な機能

- ✅ **自動翻訳ON/OFF**: システムトレイで切り替え可能
- ✅ **画面キャプチャ対応**: Win+Shift+Sでキャプチャ → 自動翻訳
- ✅ **ズーム機能**: Ctrl+マウスホイールで拡大縮小（0.1倍～5倍）
- ✅ **自動保存**: 翻訳結果を自動でimages/に保存
- ✅ **テスト機能**: 翻訳処理なしで画像表示をテスト可能

## ⚠️ 注意事項

- OpenAI gpt-image-1 APIを使用（Verified Organization必須）
- Windows 10/11 対応
- Python 3.12以上が必要