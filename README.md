# 画像翻訳ツール

16言語間で画像内テキストを自動翻訳するWindowsデスクトップアプリケーション

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

## 🚀 簡単な使い方

### 1. 言語設定
```
システムトレイアイコン右クリック → 「📝 翻訳設定」
├── 翻訳元言語 (From) ▶ 日本語、英語、タガログ語など16言語から選択
└── 翻訳先言語 (To) ▶ 英語、タガログ語、日本語など16言語から選択
```

### 2. 翻訳実行
```
1. システムトレイで自動翻訳をONにする（🔴→🟢）
2. Win+Shift+S でテキスト部分をキャプチャ
3. 進捗通知を確認（「○○語→○○語で翻訳を開始」→「AIに翻訳を依頼中...」）
4. 翻訳結果が大画面で自動表示
5. Ctrl+マウスホイールでズーム、閉じるボタンで終了
```

### 3. 対応言語例
- **日本語 → タガログ語**: ゲーム画面、マンガ、ドキュメントなど
- **英語 → 日本語**: 英語資料、Webページなど
- **中国語 → 英語**: 中国語文書の国際化など

## ⚙️ 設定

### 言語設定（システムトレイメニュー）
- **対応言語**: 16言語（日本語、英語、中国語、韓国語、タガログ語、ヨーロッパ言語など）
- **FROM/TO設定**: システムトレイ右クリック → 「📝 翻訳設定」で変更
- **デフォルト**: 日本語 → 英語

### アプリケーション設定（config/config.json）
- **翻訳品質**: medium ($0.04/枚) または high ($0.17/枚)
- **超精密モード**: アイコンやデザインの変更を防ぐ
- **画像表示設定**: ウィンドウサイズやズーム設定
- **保存設定**: ファイル名フォーマットや保存先

## 📖 詳細情報

- **利用手順**: [docs/user_guide.md](docs/user_guide.md)
- **機能仕様**: [docs/functional_requirements.md](docs/functional_requirements.md)
- **技術仕様**: [docs/detailed_design.md](docs/detailed_design.md)

## 💡 主な機能

- ✅ **16言語対応**: FROM/TO言語をシステムトレイメニューで簡単切り替え（タガログ語含む）
- ✅ **自動翻訳ON/OFF**: システムトレイで切り替え可能
- ✅ **画面キャプチャ対応**: Win+Shift+Sでキャプチャ → 自動翻訳
- ✅ **進捗通知**: 翻訳開始とAI処理中の2段階通知
- ✅ **ズーム機能**: Ctrl+マウスホイールで拡大縮小（0.1倍～5倍）
- ✅ **自動保存**: 翻訳結果を自動でimages/に保存
- ✅ **テスト機能**: 翻訳処理なしで画像表示をテスト可能

## ⚠️ 注意事項

- OpenAI gpt-image-1 APIを使用（Verified Organization必須）
- Windows 10/11 対応
- Python 3.12以上が必要