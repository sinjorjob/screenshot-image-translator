# 設定ファイル（config.json）使用ガイド

## 概要

`config.json`ファイルを編集することで、アプリケーションの動作を簡単にカスタマイズできます。

## 設定項目一覧

### 🎛️ API設定 (`api_settings`)

```json
"api_settings": {
  "quality": "medium",        // 画質: "low", "medium", "high"
  "input_fidelity": "high",   // 入力忠実度: "low", "high"
  "timeout": 120              // タイムアウト秒数
}
```

**品質とコスト**:
- `"low"`: $0.01/画像 (プロトタイプ用)
- `"medium"`: $0.04/画像 (推奨・一般用途)
- `"high"`: $0.17/画像 (最高品質・プロ用途)

### 🖼️ 画像処理設定 (`image_processing`)

```json
"image_processing": {
  "auto_padding": true,                    // 自動パディング有効
  "background_color_detection": true,      // 背景色自動検出
  "aspect_ratio_optimization": true        // アスペクト比最適化
}
```

### 🖥️ UI設定 (`ui_settings`)

```json
"ui_settings": {
  "clipboard_check_interval": 500,        // クリップボード監視間隔(ms)
  "notification_duration": 3000,          // 通知表示時間(ms)
  "window_stays_on_top": true,            // ウィンドウ最前面表示
  "max_display_width": 900,               // 最大表示幅
  "max_display_height": 700               // 最大表示高さ
}
```

### 💾 出力設定 (`output_settings`)

```json
"output_settings": {
  "auto_save": true,                              // 自動保存有効
  "save_directory": "images",                     // 保存ディレクトリ
  "filename_format": "translated_{timestamp}.png" // ファイル名フォーマット
}
```

### 📝 プロンプト設定 (`prompt_settings`)

```json
"prompt_settings": {
  "use_emoji_markers": true,              // 絵文字マーカー使用
  "precision_level": "ultra",             // 精度レベル
  "language_pair": "ja_to_en"             // 言語ペア
}
```

### 🐛 デバッグ設定 (`debug_settings`)

```json
"debug_settings": {
  "log_level": "INFO",                    // ログレベル
  "detailed_logging": true,               // 詳細ログ有効
  "save_padded_images": false             // パディング画像保存
}
```

## よくある設定例

### 💰 コスト重視設定
```json
{
  "api_settings": {
    "quality": "low",
    "input_fidelity": "low",
    "timeout": 60
  }
}
```

### 🎨 品質重視設定
```json
{
  "api_settings": {
    "quality": "high",
    "input_fidelity": "high",
    "timeout": 180
  }
}
```

### ⚡ 高速動作設定
```json
{
  "ui_settings": {
    "clipboard_check_interval": 250,
    "notification_duration": 1500
  },
  "api_settings": {
    "timeout": 60
  }
}
```

### 🎯 デバッグ設定
```json
{
  "debug_settings": {
    "log_level": "DEBUG",
    "detailed_logging": true,
    "save_padded_images": true
  }
}
```

## 設定の変更方法

1. `config.json`ファイルをテキストエディタで開く
2. 変更したい項目の値を編集
3. ファイルを保存
4. アプリケーションを再起動

## 注意事項

- ⚠️ JSON形式が正しくない場合、デフォルト設定が使用されます
- 💰 `quality: "high"`は高コストです（$0.17/画像）
- 🔄 設定変更後はアプリケーションの再起動が必要です
- 📁 `save_directory`が存在しない場合は自動作成されます

## トラブルシューティング

### 設定が反映されない
1. JSON形式をチェック（[JSONLint](https://jsonlint.com/)等で検証）
2. アプリケーションを完全に再起動
3. ログファイルでエラーメッセージを確認

### コストが予想より高い
- `quality`設定を確認
- `"medium"`推奨（バランス良好）
- 使用頻度を考慮して設定調整