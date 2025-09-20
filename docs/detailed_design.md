# 画像翻訳ツール 詳細設計書
## 1. システム概要

### 1.1 シンプルなアーキテクチャ
```
┌───────────────────────────────┐
│     クリップボード監視          │
│         ↓                     │
│     画像検出                  │
│         ↓                     │
│   GPT-Image-1 API送信         │
│         ↓                     │
│     結果表示ウィンドウ          │
└───────────────────────────────┘
```

### 1.2 ファイル構成
```
画像翻訳ツール/
├── README.md              # プロジェクト概要
├── requirements.txt       # Python依存パッケージ
├── .env                   # 環境変数（APIキー）
├── .env.example          # 環境変数テンプレート
├── config/               # 設定ファイル
│   └── config.json      # アプリケーション設定
├── source/              # ソースコード
│   ├── main.py         # メインプログラム
│   └── assets/         # 静的リソース
│       └── icons/      # アプリアイコン
│           ├── ON.png  # 自動翻訳ON時
│           └── OFF.png # 自動翻訳OFF時
├── images/              # 翻訳結果画像（自動生成）
├── logs/                # ログファイル（自動生成）
└── docs/               # ドキュメント
    ├── user_guide.md
    ├── functional_requirements.md
    ├── detailed_design.md
    └── config_guide.md
```

## 2. 主要クラス設計

### 2.1 TranslationThread クラス
- **目的**: 画像翻訳処理の非同期実行
- **主要機能**:
  - アスペクト比最適化とパディング処理
  - GPT-Image-1 API呼び出し（メイン・フォールバック方式）
  - 超精密モード対応（PHOTOCOPY MODE）
  - パディング除去・元サイズ復元
  - 詳細ログ記録

### 2.2 ResultWindow / ZoomableImageLabel クラス
- **目的**: 翻訳結果の大画面表示
- **主要機能**:
  - Ctrl+マウスホイールによるズーム（0.1倍～5倍）
  - スクロール機能（拡大時の画像移動）
  - リアルタイムズーム表示
  - 大きな文字とボタンによる見やすいUI

### 2.3 ImageTranslatorApp クラス
- **目的**: メインアプリケーション制御
- **主要機能**:
  - クリップボード監視（設定可能な間隔）
  - **翻訳言語設定機能**（16言語対応、FROM/TO個別選択、動的メニュー生成）
  - 自動翻訳ON/OFF切り替え機能
  - **進捗通知システム**（シンプル化された2段階進捗表示）
  - システムトレイ管理（アイコン状態表示、階層式言語設定メニュー、テスト表示機能付き）
  - 古いクリップボード画像処理防止機能
  - 自動保存機能
  - 設定ファイル管理（config/config.json）

### 2.4 言語切り替えシステム
- **目的**: 16言語間での自由な翻訳言語設定
- **主要機能**:
  - 動的言語マッピング（display名、API名、prompt名の管理）
  - システムトレイ階層メニュー（FROM言語、TO言語の個別選択）
  - 同一言語選択防止機能
  - 設定の永続化（config.jsonへの自動保存）
  - 意味理解型翻訳（言語名の正確な翻訳）
  - リアルタイム設定反映

### 2.5 進捗通知システム
- **目的**: ユーザーへの翻訳処理状況の明確な通知
- **主要機能**:
  - 翻訳開始通知（言語ペア表示：「日本語→タガログ語で翻訳を開始」）
  - AI処理通知（「AIに翻訳を依頼中...」）
  - エラー時の詳細通知とダイアログ表示
  - 通知の簡潔性重視（不要な前処理通知を削除）

## 3. 設定システム

### 3.1 config.json ファイル
```json
{
  "translation_settings": {
    "from_language": "japanese",
    "to_language": "english"
  },
  "api_settings": {
    "quality": "medium",
    "input_fidelity": "high",
    "timeout": 120,
    "ultra_precision_mode": true
  },
  "image_processing": {
    "auto_padding": true,
    "background_color_detection": true,
    "aspect_ratio_optimization": true
  },
  "ui_settings": {
    "clipboard_check_interval": 500,
    "notification_duration": 3000,
    "window_stays_on_top": true,
    "max_display_width": 1400,
    "max_display_height": 1000
  },
  "output_settings": {
    "auto_save": true,
    "save_directory": "images",
    "filename_format": "translated_{timestamp}.png"
  }
}
```

### 3.2 .env ファイル
```env
# OpenAI APIキー
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3.3 requirements.txt
```txt
PyQt5==5.15.9
Pillow==10.0.0
requests==2.31.0
python-dotenv==1.0.0
```

## 4. インストールと実行手順

### 4.1 セットアップ
```bash
# 1. 必要なパッケージをインストール
pip install -r requirements.txt

# 2. .envファイルを作成してAPIキーを設定
echo "OPENAI_API_KEY=your-api-key-here" > .env

# 3. アプリケーション実行
python main.py
```

### 4.2 使用方法
1. アプリケーションを起動（システムトレイに常駐）
2. Windows標準のスクリーンショット機能（Win+Shift+S）で画面をキャプチャ
3. 自動的に翻訳処理が開始
4. 翻訳結果がウィンドウに表示される
5. 「閉じる」ボタンで結果ウィンドウを閉じる
6. システムトレイアイコンを右クリック→「終了」でアプリ終了

## 5. 主要な処理フロー

### 5.1 クリップボード監視
```python
# 500ms間隔でクリップボードをチェック
def check_clipboard(self):
    mime_data = self.clipboard.mimeData()
    if mime_data.hasImage():
        # 画像検出 → 翻訳処理へ
```

### 5.2 API呼び出し（強化版）
```python
# アスペクト比保持のパディング処理
processed_image, padding_info = self.prepare_image_with_padding(image)

# 超精密モード対応のPHOTOCOPY MODE プロンプト
optimized_prompt = self.create_optimized_prompt(image.size, size, padding_info)

# multipart/form-data形式でのAPI呼び出し
files = [('image[]', ('image.png', img_buffer.getvalue(), 'image/png'))]
data = {
    'model': 'gpt-image-1',
    'prompt': optimized_prompt,
    'size': size,
    'quality': quality,  # medium/high（超精密モード時は自動でhigh）
    'input_fidelity': input_fidelity,
    'n': 1
}

response = requests.post(
    "https://api.openai.com/v1/images/edits",
    headers=headers,
    files=files,
    data=data,
    timeout=timeout
)

# パディング除去・元サイズ復元
final_image = self.remove_padding_and_restore_size(
    translated_image, image.size, padding_info
)
```

### 5.3 非同期処理
```python
# QThreadを使用してUIをブロックしない
class TranslationThread(QThread):
    def run(self):
        # 重い処理（API呼び出し）を別スレッドで実行
```

## 6. エラーハンドリング

### 6.1 基本的なエラー処理
- **APIキー未設定**: 起動時にチェックしてエラーメッセージ表示
- **API通信エラー**: QMessageBoxでユーザーに通知
- **タイムアウト**: 30秒でタイムアウト設定
- **画像変換エラー**: try-exceptでキャッチして継続

### 6.2 エラー時の動作
```python
def on_translation_error(self, error_message):
    # エラーダイアログ表示
    QMessageBox.critical(None, "エラー", error_message)
    # 処理は継続（次のクリップボード画像を待機）
```

## 7. 制限事項と注意点

### 7.1 技術的制限
- GPT-Image-1が自動的にテキスト領域を認識するため、マスク指定は不要
- OCR処理も不要（AIが画像内の日本語テキストを自動認識）
- 画像サイズは1024x1024、1536x1024、1024x1536の3種類に自動調整
- アスペクト比保持のためのパディング処理が必要

### 7.2 使用上の注意
- APIキーは.envファイルに保存（Gitにはコミットしない）
- 料金: medium品質 $0.04/枚、high品質 $0.17/枚
- 超精密モード時は自動的にhigh品質を使用
- 同じ画像の重複処理を防ぐため、画像ハッシュによる比較を実装
- 翻訳結果は自動的にimagesフォルダに保存
- 詳細ログがlogsフォルダに記録される

### 7.3 新機能
- **自動翻訳ON/OFF機能**: デフォルトOFF、システムトレイで切り替え、不要なAPI処理を防止
- **カスタムアイコン**: ON.png/OFF.pngによる視覚的状態表示
- **古い画像処理防止**: ON切り替え時にクリップボード画像ハッシュを更新し、新しい画像のみ処理
- **画像表示テスト機能**: システムトレイから任意の画像を表示テスト可能
- **ズーム機能**: Ctrl+マウスホイールで0.1倍～5倍まで拡大縮小
- **パディング除去**: 翻訳後に無駄な余白を自動除去して元サイズに復元
- **超精密モード**: アイコンやデザインの変更を防ぐFORBIDDEN ZONE設定
- **16言語対応翻訳設定**: FROM/TO言語の個別選択（タガログ語含む）、システムトレイ階層メニュー
- **意味理解型翻訳**: 言語名の正確な翻訳（例：「日本語」→「wikang Hapon」）
- **進捗通知シンプル化**: 2段階進捗表示（翻訳開始、AI処理中）でユーザビリティ向上


---

*作成日: 2025年1月16日*
*バージョン: 2.0*
*変更内容: 最小限の機能に絞った実装に変更*