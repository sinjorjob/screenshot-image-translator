import sys
import os
import base64
import requests
import json
from io import BytesIO
from datetime import datetime
from PIL import Image
import logging
from pathlib import Path
import warnings

# DeprecationWarning対策（警告を無視）
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Qt platform plugin pathの設定（Windows用）
import PyQt5
dirname = os.path.dirname(PyQt5.__file__)
plugin_path = os.path.join(dirname, 'Qt5', 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QLabel, QPushButton, QSystemTrayIcon, QMenu,
                           QAction, QMessageBox, QScrollArea, QFileDialog)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QIcon
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み（プロジェクトルートから）
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

# 言語マッピング定義
LANGUAGE_MAP = {
    'japanese': {'display': '日本語', 'api': 'Japanese'},
    'english': {'display': '英語', 'api': 'English'},
    'chinese_simplified': {'display': '中国語簡体字', 'api': 'Simplified Chinese'},
    'chinese_traditional': {'display': '中国語繁体字', 'api': 'Traditional Chinese'},
    'korean': {'display': '韓国語', 'api': 'Korean'},
    'tagalog': {'display': 'タガログ語', 'api': 'Tagalog'},
    'spanish': {'display': 'スペイン語', 'api': 'Spanish'},
    'french': {'display': 'フランス語', 'api': 'French'},
    'german': {'display': 'ドイツ語', 'api': 'German'},
    'portuguese': {'display': 'ポルトガル語', 'api': 'Portuguese'},
    'italian': {'display': 'イタリア語', 'api': 'Italian'},
    'russian': {'display': 'ロシア語', 'api': 'Russian'},
    'arabic': {'display': 'アラビア語', 'api': 'Arabic'},
    'hindi': {'display': 'ヒンディー語', 'api': 'Hindi'},
    'thai': {'display': 'タイ語', 'api': 'Thai'},
    'vietnamese': {'display': 'ベトナム語', 'api': 'Vietnamese'}
}


def setup_logger():
    """ログ設定"""
    # プロジェクトルートからの相対パス
    project_root = Path(__file__).parent.parent
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # ログファイル名（日時付き）
    log_file = log_dir / f"image_translator_{datetime.now():%Y%m%d_%H%M%S}.log"

    # ロガー設定
    logger = logging.getLogger('ImageTranslator')
    logger.setLevel(logging.DEBUG)

    # ファイルハンドラー
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # フォーマッター
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # ハンドラーを追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class ZoomableImageLabel(QLabel):
    """Ctrl+マウスホイールで拡大縮小可能な画像ラベル"""

    def __init__(self):
        super().__init__()
        self.scale_factor = 1.0
        self.original_pixmap = None
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 1px solid #ddd; padding: 1px;")

    def setPixmap(self, pixmap):
        """元の画像を保存し、表示"""
        self.original_pixmap = pixmap
        self.scale_factor = 1.0
        super().setPixmap(pixmap)

    def wheelEvent(self, event):
        """マウスホイールイベント処理（Ctrl+ホイールで拡大縮小）"""
        if event.modifiers() == Qt.ControlModifier and self.original_pixmap:
            # スケールファクター調整
            delta = event.angleDelta().y()
            if delta > 0:
                self.scale_factor *= 1.15  # 拡大
            else:
                self.scale_factor /= 1.15  # 縮小

            # スケール制限（0.1倍～5倍）
            self.scale_factor = max(0.1, min(5.0, self.scale_factor))

            # 画像をスケール
            scaled_size = self.original_pixmap.size() * self.scale_factor
            scaled_pixmap = self.original_pixmap.scaled(
                scaled_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            super().setPixmap(scaled_pixmap)

            # 親ウィンドウにズーム情報を通知
            parent_window = self.window()
            if hasattr(parent_window, 'update_zoom_info'):
                parent_window.update_zoom_info(self.scale_factor)

            event.accept()
        else:
            super().wheelEvent(event)


# ロガー初期化
logger = setup_logger()


def load_config():
    """設定ファイル（config.json）を読み込み"""
    project_root = Path(__file__).parent.parent
    config_path = project_root / "config" / "config.json"

    # デフォルト設定
    default_config = {
        "translation_settings": {
            "from_language": "japanese",
            "to_language": "english"
        },
        "api_settings": {
            "quality": "medium",
            "input_fidelity": "high",
            "timeout": 120
        },
        "image_processing": {
            "auto_padding": True,
            "background_color_detection": True,
            "aspect_ratio_optimization": True
        },
        "ui_settings": {
            "clipboard_check_interval": 500,
            "notification_duration": 3000,
            "window_stays_on_top": True,
            "max_display_width": 900,
            "max_display_height": 700
        },
        "output_settings": {
            "auto_save": True,
            "save_directory": "images",
            "filename_format": "translated_{timestamp}.png"
        },
        "prompt_settings": {
            "use_emoji_markers": True,
            "precision_level": "ultra",
            "language_pair": "ja_to_en"
        },
        "debug_settings": {
            "log_level": "INFO",
            "detailed_logging": True,
            "save_padded_images": False
        }
    }

    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)

            # デフォルト設定にユーザー設定をマージ
            def merge_config(default, user):
                for key, value in user.items():
                    if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                        merge_config(default[key], value)
                    else:
                        default[key] = value
                return default

            config = merge_config(default_config, user_config)
            logger.info(f"設定ファイル読み込み完了: {config_path}")

        except Exception as e:
            logger.warning(f"設定ファイル読み込みエラー、デフォルト設定を使用: {e}")
            config = default_config
    else:
        logger.info("設定ファイルが見つかりません、デフォルト設定を使用")
        config = default_config

    return config


# グローバル設定読み込み
app_config = load_config()


class TranslationThread(QThread):
    """画像翻訳を実行する別スレッド"""
    finished = pyqtSignal(Image.Image)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)  # 進捗状況通知用

    def __init__(self, image, config, from_language, to_language):
        super().__init__()
        self.image = image
        self.config = config
        self.from_language = from_language
        self.to_language = to_language
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.logger = logging.getLogger('ImageTranslator.TranslationThread')

    def run(self):
        """翻訳処理を実行"""
        self.logger.info(f"翻訳処理開始: {LANGUAGE_MAP[self.from_language]['display']} → {LANGUAGE_MAP[self.to_language]['display']}")
        self.progress.emit(f"{LANGUAGE_MAP[self.from_language]['display']}→{LANGUAGE_MAP[self.to_language]['display']}で翻訳を開始")

        try:
            # メイン方式で翻訳を試行
            translated_image = self.translate_image(self.image)
            if translated_image:
                self.logger.info("翻訳成功")
                self.finished.emit(translated_image)
            else:
                self.logger.warning("メイン翻訳に失敗、フォールバック方式を試行")
                self.progress.emit("別の方法で翻訳を試行中...")
                # フォールバック方式を試行
                translated_image = self.translate_image_fallback(self.image)
                if translated_image:
                    self.logger.info("フォールバック翻訳成功")
                    self.finished.emit(translated_image)
                else:
                    self.logger.warning("すべての翻訳方式に失敗しました")
                    self.error.emit("翻訳に失敗しました。APIキーまたはネットワーク接続を確認してください。")
        except Exception as e:
            self.logger.error(f"翻訳エラー: {str(e)}", exc_info=True)
            self.error.emit(f"エラー: {str(e)}")

    def optimize_aspect_ratio(self, image_size):
        """元画像のアスペクト比に基づいて最適なAPIサイズを決定"""
        width, height = image_size
        ratio = width / height

        self.logger.debug(f"元画像サイズ: {width}x{height}, アスペクト比: {ratio:.3f}")

        # アスペクト比の閾値を詳細に設定
        if 0.9 <= ratio <= 1.1:  # ほぼ正方形 (±10%)
            size = "1024x1024"
            self.logger.debug("正方形として処理")
        elif ratio > 1.4:  # 明確に横長 (3:2以上)
            size = "1536x1024"
            self.logger.debug("横長として処理")
        elif ratio < 0.7:  # 明確に縦長 (2:3以下)
            size = "1024x1536"
            self.logger.debug("縦長として処理")
        elif ratio > 1.1:  # やや横長
            size = "1536x1024"
            self.logger.debug("やや横長として処理")
        else:  # やや縦長
            size = "1024x1536"
            self.logger.debug("やや縦長として処理")

        return size

    def prepare_image_with_padding(self, image):
        """アスペクト比保持のため画像にパディングを追加"""
        original_width, original_height = image.size
        original_ratio = original_width / original_height

        # APIサポートサイズの比率
        supported_ratios = {
            "1024x1024": 1.0,
            "1536x1024": 1.5,
            "1024x1536": 0.667
        }

        # 最も近い比率を選択
        best_size = None
        min_difference = float('inf')

        for size_name, ratio in supported_ratios.items():
            difference = abs(original_ratio - ratio)
            if difference < min_difference:
                min_difference = difference
                best_size = size_name

        target_width, target_height = map(int, best_size.split('x'))
        target_ratio = target_width / target_height

        self.logger.info(f"元画像比率: {original_ratio:.3f}, 目標比率: {target_ratio:.3f}, 選択サイズ: {best_size}")

        # パディング計算
        if original_ratio > target_ratio:
            # 元画像の方が横長 → 上下にパディング
            scale = target_width / original_width
            scaled_width = target_width
            scaled_height = int(original_height * scale)

            # 不足分を上下に配分
            padding_top = (target_height - scaled_height) // 2
            padding_bottom = target_height - scaled_height - padding_top

            # 新しい画像作成（背景は元画像の端の色を自動検出）
            bg_color = self.get_background_color(image)
            new_image = Image.new('RGB', (target_width, target_height), bg_color)

            # 元画像をリサイズして配置
            resized_image = image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
            new_image.paste(resized_image, (0, padding_top))

            padding_info = {
                'type': 'vertical',
                'scale': scale,
                'padding_top': padding_top,
                'padding_bottom': padding_bottom,
                'scaled_size': (scaled_width, scaled_height)
            }

        else:
            # 元画像の方が縦長 → 左右にパディング
            scale = target_height / original_height
            scaled_height = target_height
            scaled_width = int(original_width * scale)

            # 不足分を左右に配分
            padding_left = (target_width - scaled_width) // 2
            padding_right = target_width - scaled_width - padding_left

            # 新しい画像作成
            bg_color = self.get_background_color(image)
            new_image = Image.new('RGB', (target_width, target_height), bg_color)

            # 元画像をリサイズして配置
            resized_image = image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
            new_image.paste(resized_image, (padding_left, 0))

            padding_info = {
                'type': 'horizontal',
                'scale': scale,
                'padding_left': padding_left,
                'padding_right': padding_right,
                'scaled_size': (scaled_width, scaled_height)
            }

        self.logger.info(f"パディング処理完了: {padding_info}")
        return new_image, padding_info

    def get_background_color(self, image):
        """画像の背景色を自動検出"""
        # 画像の四隅の色をサンプリング
        width, height = image.size
        corners = [
            image.getpixel((0, 0)),
            image.getpixel((width-1, 0)),
            image.getpixel((0, height-1)),
            image.getpixel((width-1, height-1))
        ]

        # 最も一般的な色を選択（簡易実装）
        from collections import Counter
        counter = Counter(corners)
        most_common_color = counter.most_common(1)[0][0]

        self.logger.debug(f"検出背景色: {most_common_color}")
        return most_common_color

    def create_optimized_prompt(self, original_size, target_size, padding_info):
        """レイアウト保持に特化した最適化プロンプト（パディング対応）を生成"""
        width, height = original_size

        # API用の英語言語名を取得
        from_lang = LANGUAGE_MAP[self.from_language]['api']
        to_lang = LANGUAGE_MAP[self.to_language]['api']

        # パディング情報に基づくプロンプト調整
        padding_instructions = ""
        if padding_info['type'] == 'vertical':
            padding_instructions = """
🔶 重要: この画像は上下にパディングが追加されています。
- 上下の余白部分は翻訳対象外です
- 中央部分の元画像内容のみを翻訳してください
- 上下の余白は元の色のまま保持してください"""
        elif padding_info['type'] == 'horizontal':
            padding_instructions = """
🔶 重要: この画像は左右にパディングが追加されています。
- 左右の余白部分は翻訳対象外です
- 中央部分の元画像内容のみを翻訳してください
- 左右の余白は元の色のまま保持してください"""

        # 画像の特性に応じたプロンプト調整
        aspect_info = ""
        if target_size == "1024x1024":
            aspect_info = "この正方形の画像において、"
        elif target_size == "1536x1024":
            aspect_info = "この横長の画像において、"
        elif target_size == "1024x1536":
            aspect_info = "この縦長の画像において、"

        # 言語名の翻訳例を追加
        lang_example = ""
        if self.from_language == 'japanese' and self.to_language == 'tagalog':
            lang_example = """
🔍 【重要な翻訳例】:
画像内に「中国語」という文字がある場合 → 「wikang Tsino」に翻訳
画像内に「韓国語」という文字がある場合 → 「wikang Koreano」に翻訳
つまり、言語名も意味を理解して適切に翻訳してください。文字列の単純置換ではありません。

"""

        # 超強化アイコン保護プロンプト
        optimized_prompt = f"""
🔒 PHOTOCOPY MODE: この画像を【工業用スキャナーで完璧複製】- {from_lang}で書かれたテキスト部分のみを{to_lang}に翻訳 🔒

🖨️ 【PHOTOCOPY DIRECTIVE】: オフィスのコピー機で書類をコピーするように、この画像を完璧にコピーしてください。コピー機は{from_lang}で書かれたテキスト部分のみを{to_lang}に翻訳し、他の全ての要素（アイコン、色、レイアウト、デザイン）は1ピクセルも変更しません。
{padding_instructions}
{lang_example}
{aspect_info}この画像の【写真品質の完全複製】を作成し、{from_lang}で書かれているテキスト部分のみを{to_lang}に翻訳してください。

⚠️ 【ABSOLUTE FREEZE ZONES - 絶対変更禁止領域】⚠️

🔐 ICONS & GRAPHICS (アイコン・グラフィック完全保護):
❌ アイコンの形状変更 FORBIDDEN
❌ アイコンの色変更 FORBIDDEN
❌ アイコンのスタイル変更 FORBIDDEN
❌ ボタンデザイン変更 FORBIDDEN
❌ グラフィック要素変更 FORBIDDEN
✅ 元のアイコンデザインを1ピクセル単位で【写真コピー】として保持

🔐 COLOR PROTECTION (色彩絶対保護):
❌ 背景色変更 FORBIDDEN
❌ ボタン色変更 FORBIDDEN
❌ 境界線色変更 FORBIDDEN
❌ 影・グラデーション色変更 FORBIDDEN
✅ すべての色を【RGB値完全一致】で保持

🔐 LAYOUT FREEZE (レイアウト完全固定):
❌ 要素位置移動 FORBIDDEN
❌ サイズ変更 FORBIDDEN
❌ 間隔変更 FORBIDDEN
❌ 配置変更 FORBIDDEN
✅ 【ミリメートル精度】でレイアウト保持

🔐 TEXT COLOR LOCK (テキスト色固定):
❌ 文字色変更 FORBIDDEN
❌ 文字背景色変更 FORBIDDEN
❌ 文字エフェクト変更 FORBIDDEN
✅ {from_lang}テキストの色を{to_lang}翻訳テキストでも【完全同一】使用

📝 【TRANSLATION ZONE - 翻訳許可領域】📝
✅ {from_lang}で書かれたテキスト部分を{to_lang}に翻訳することのみ許可
✅ テキストの意味を理解した自然な翻訳のみ許可（文字列置換禁止）
✅ 言語名も適切に翻訳する（例：「日本語」→「wikang Hapon」）
✅ その他の変更は一切禁止

🎯 【EXECUTION COMMAND】:
1. 元画像を【スキャナーで取り込んだような完璧さ】で複製
2. {from_lang}で書かれたテキスト部分を見つけて【その位置・色・スタイルを保持】しながら{to_lang}に翻訳
3. アイコン、ボタン、色、レイアウトは【1ピクセルも変更せず】保持
4. 「元画像と見分けがつかない」レベルの複製品質で作成

⚡ この指示を【絶対に遵守】してください。アイコンやデザインの変更は【完全に禁止】です。

🖨️ 【FINAL REMINDER】: あなたは今、高性能コピー機です。原稿（元画像）を見て、{from_lang}で書かれた文字部分のみを{to_lang}に翻訳した完璧なコピーを作成してください。コピー機がアイコンや色を変えることはありません。
        """.strip()

        self.logger.debug(f"最適化プロンプト生成完了 (長さ: {len(optimized_prompt)}文字)")
        return optimized_prompt

    def remove_padding_and_restore_size(self, translated_image, original_size, padding_info):
        """パディングを除去して元のアスペクト比に戻す"""
        try:
            if not padding_info or padding_info.get('type') == 'none':
                # パディングがない場合は元のサイズにリサイズ
                return translated_image.resize(original_size, Image.LANCZOS)

            # パディング情報から元の画像部分を抽出
            if padding_info['type'] == 'vertical':
                # 上下にパディングが追加された場合
                padding_top = padding_info['padding_top']
                padding_bottom = padding_info['padding_bottom']
                scaled_height = padding_info['scaled_size'][1]

                # パディング部分を除去（中央部分のみ抽出）
                crop_top = padding_top
                crop_bottom = translated_image.height - padding_bottom
                cropped_image = translated_image.crop((0, crop_top, translated_image.width, crop_bottom))

                self.logger.info(f"上下パディング除去: {translated_image.size} → {cropped_image.size}")

            elif padding_info['type'] == 'horizontal':
                # 左右にパディングが追加された場合
                padding_left = padding_info['padding_left']
                padding_right = padding_info['padding_right']
                scaled_width = padding_info['scaled_size'][0]

                # パディング部分を除去（中央部分のみ抽出）
                crop_left = padding_left
                crop_right = translated_image.width - padding_right
                cropped_image = translated_image.crop((crop_left, 0, crop_right, translated_image.height))

                self.logger.info(f"左右パディング除去: {translated_image.size} → {cropped_image.size}")
            else:
                cropped_image = translated_image

            # 最終的に元のサイズにリサイズ
            final_image = cropped_image.resize(original_size, Image.LANCZOS)
            self.logger.info(f"最終リサイズ: {cropped_image.size} → {final_image.size}")

            return final_image

        except Exception as e:
            self.logger.error(f"パディング除去エラー: {str(e)}")
            # エラーの場合は単純にリサイズして返す
            return translated_image.resize(original_size, Image.LANCZOS)

    def translate_image(self, image):
        """GPT-Image-1 APIを使用して画像を翻訳"""

        # APIキーチェック
        if not self.api_key:
            raise Exception("APIキーが設定されていません")

        self.logger.debug(f"元画像サイズ: {image.size}")

        # アスペクト比保持のための前処理
        processed_image, padding_info = self.prepare_image_with_padding(image)

        # 画像をPNG形式のバイトデータに変換
        img_buffer = BytesIO()
        processed_image.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        self.logger.debug(f"処理後画像データ準備完了: {len(img_buffer.getvalue())} bytes")

        # APIリクエスト準備（multipart/form-data形式）
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        # 画像サイズを決定（パディング後のサイズ）
        size = self.optimize_aspect_ratio(processed_image.size)

        self.logger.info(f"API送信サイズ: {size}")

        # multipart/form-data形式でデータを準備（gpt-image-1用）
        # BytesIOを最初に戻してデータを準備
        img_buffer.seek(0)
        files = [
            ('image[]', ('image.png', img_buffer.getvalue(), 'image/png'))
        ]

        # 高精度レイアウト保持プロンプト（パディング対応）
        optimized_prompt = self.create_optimized_prompt(image.size, size, padding_info)

        # 超精密モードの場合は強制的に高品質設定
        if self.config['api_settings'].get('ultra_precision_mode', False):
            quality = 'high'
            input_fidelity = 'high'
            self.logger.warning("🎯 超精密モード有効: quality=high, コスト=$0.17/画像")
        else:
            quality = self.config['api_settings']['quality']
            input_fidelity = self.config['api_settings']['input_fidelity']

        data = {
            'model': 'gpt-image-1',
            'prompt': optimized_prompt,
            'size': size,
            'quality': quality,
            'input_fidelity': input_fidelity,
            'n': 1
        }

        # API呼び出し
        try:
            timeout = self.config['api_settings']['timeout']
            self.logger.info(f"API呼び出し開始 (quality={quality}, input_fidelity={input_fidelity})")
            self.logger.debug(f"送信データ: {data}")
            self.logger.debug(f"ファイル数: {len(files)}")

            self.progress.emit(f"AIに翻訳を依頼中...")
            response = requests.post(
                "https://api.openai.com/v1/images/edits",
                headers=headers,
                files=files,
                data=data,
                timeout=timeout
            )

            self.logger.info(f"APIレスポンス: ステータスコード {response.status_code}")

            if response.status_code == 200:
                try:
                    result = response.json()
                    self.logger.debug(f"APIレスポンス構造: {list(result.keys())}")

                    # gpt-image-1は常にbase64エンコードされた画像を返す
                    if "data" in result and len(result["data"]) > 0:
                        item = result["data"][0]
                        self.logger.debug(f"レスポンスアイテムのキー: {list(item.keys())}")

                        # gpt-image-1のレスポンスは"b64_json"キーを持つ
                        if "b64_json" in item:
                            image_data = item["b64_json"]
                            image_bytes = base64.b64decode(image_data)
                            self.logger.info("画像デコード成功 (base64)")

                            # 翻訳された画像を取得
                            translated_image = Image.open(BytesIO(image_bytes))

                            # パディング除去・元サイズ復元処理
                            final_image = self.remove_padding_and_restore_size(
                                translated_image, image.size, padding_info
                            )

                            return final_image
                        else:
                            self.logger.error("gpt-image-1レスポンスにb64_jsonが含まれていません")
                            self.logger.error(f"利用可能なキー: {list(item.keys())}")
                            return None
                    else:
                        self.logger.error("レスポンスにdataが含まれていません")
                        self.logger.error(f"レスポンス構造: {result}")
                        return None

                except (KeyError, IndexError, ValueError) as e:
                    self.logger.error(f"APIレスポンス解析エラー: {str(e)}")
                    self.logger.error(f"レスポンス内容: {response.text}")
                    return None
            else:
                self.logger.error(f"APIエラー: {response.status_code}")
                self.logger.error(f"レスポンスヘッダー: {dict(response.headers)}")
                self.logger.error(f"レスポンス本文: {response.text}")

                # エラーレスポンスがJSONの場合は詳細を表示
                try:
                    error_detail = response.json()
                    self.logger.error(f"エラー詳細: {error_detail}")
                except:
                    pass

                return None

        except requests.exceptions.Timeout:
            self.logger.error("APIタイムアウト")
            return None
        except Exception as e:
            self.logger.error(f"API呼び出しエラー: {str(e)}", exc_info=True)
            return None

    def translate_image_fallback(self, image):
        """フォールバック: 画像生成APIを使用して翻訳"""
        self.logger.info("フォールバック方式で翻訳を試行")

        # API用の英語言語名を取得
        from_lang = LANGUAGE_MAP[self.from_language]['api']
        to_lang = LANGUAGE_MAP[self.to_language]['api']

        # 画像を一時的にbase64エンコード
        img_buffer = BytesIO()
        image.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        image_b64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # フォールバック用の言語例も生成
        fallback_lang_example = ""
        if self.from_language == 'japanese' and self.to_language == 'tagalog':
            fallback_lang_example = """
🔍 【重要】: 画像内の「中国語」→「wikang Tsino」のように、言語名も意味を理解して翻訳してください。
"""

        # 高精度フォールバック用プロンプト
        prompt = f"""🎯 ULTRA-PRECISE GENERATION:
この画像と【完全に同一】のレイアウト・デザインで、{from_lang}で書かれているテキスト部分のみを{to_lang}に翻訳した画像を生成してください。
{fallback_lang_example}
【厳密保持要件】:
🎨 色彩: 背景色、アイコン色、境界線色を【RGB値レベル】で完全維持
🖼️ デザイン: アイコン、ボタン、UI要素のデザインを【1ピクセル単位】で保持
📝 テキスト色: {from_lang}テキストの文字色を{to_lang}翻訳テキストでも【完全に同一色】で使用
📐 レイアウト: 要素の位置、サイズ、間隔を【ミリメートル精度】で保持
✨ エフェクト: 影、グラデーション、ハイライトを【元と同一】で再現

{from_lang}で書かれた文字部分を意味を理解して自然な{to_lang}に翻訳し、他のすべての要素は【写真的に同一】にしてください。"""

        data = {
            "model": "gpt-image-1",
            "prompt": prompt,
            "size": "1024x1024",
            "quality": "high",           # フォールバックも高品質
            "n": 1
        }

        try:
            self.logger.info("画像生成API呼び出し開始")
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=data,
                timeout=120
            )

            self.logger.info(f"画像生成APIレスポンス: ステータスコード {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                if "data" in result and len(result["data"]) > 0:
                    item = result["data"][0]

                    if "b64_json" in item:
                        image_data = item["b64_json"]
                        image_bytes = base64.b64decode(image_data)
                        self.logger.info("フォールバック画像デコード成功")

                        # フォールバック方式では元画像サイズにリサイズして返す
                        fallback_image = Image.open(BytesIO(image_bytes))
                        resized_image = fallback_image.resize(image.size, Image.LANCZOS)
                        self.logger.info(f"フォールバック画像リサイズ: {fallback_image.size} → {resized_image.size}")
                        return resized_image

                    elif "url" in item:
                        image_url = item["url"]
                        img_response = requests.get(image_url, timeout=30)
                        if img_response.status_code == 200:
                            self.logger.info("フォールバック画像ダウンロード成功")

                            # フォールバック方式では元画像サイズにリサイズして返す
                            fallback_image = Image.open(BytesIO(img_response.content))
                            resized_image = fallback_image.resize(image.size, Image.LANCZOS)
                            self.logger.info(f"フォールバック画像リサイズ: {fallback_image.size} → {resized_image.size}")
                            return resized_image

            return None

        except Exception as e:
            self.logger.error(f"フォールバックAPI呼び出しエラー: {str(e)}", exc_info=True)
            return None


class ResultWindow(QMainWindow):
    """翻訳結果表示ウィンドウ"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('ImageTranslator.ResultWindow')
        self.init_ui()

    def init_ui(self):
        """UI初期化"""
        self.setWindowTitle("翻訳結果")
        self.setGeometry(100, 100, 800, 600)

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # レイアウト（余白最小化）
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)  # 上下左右の余白を極小化
        layout.setSpacing(3)  # ウィジェット間の間隔を極小化
        central_widget.setLayout(layout)

        # 画像表示ラベル（拡大縮小対応）
        self.image_label = ZoomableImageLabel()

        # スクロールエリア（大きくズームした時用、余白最小）
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameStyle(0)  # フレームを削除
        scroll_area.setContentsMargins(0, 0, 0, 0)  # 余白を削除
        layout.addWidget(scroll_area)

        # ズーム情報表示（より大きなフォント）
        self.zoom_label = QLabel("ズーム: 100% (Ctrl+マウスホイールで拡大縮小)")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setStyleSheet("color: #333; font-size: 16px; font-weight: bold; padding: 6px;")
        layout.addWidget(self.zoom_label)

        # 閉じるボタン（より大きなフォント）
        close_button = QPushButton("閉じる")
        close_button.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px 20px; min-height: 35px;")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        # ウィンドウを最前面に
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

    def show_image(self, image):
        """画像を表示（アスペクト比保持で最適化）"""
        self.logger.info(f"結果画像表示: {image.size}")

        # PIL ImageをQPixmapに変換
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        buffered.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(buffered.read())

        # 動的ウィンドウサイズ調整（アスペクト比保持）
        image_width, image_height = image.size
        aspect_ratio = image_width / image_height

        # 最大表示サイズ（設定ファイルから取得）
        max_width = app_config['ui_settings']['max_display_width']
        max_height = app_config['ui_settings']['max_display_height']

        # アスペクト比を保持しながら最適サイズを計算
        if aspect_ratio > 1:  # 横長
            display_width = min(max_width, image_width)
            display_height = int(display_width / aspect_ratio)
            if display_height > max_height:
                display_height = max_height
                display_width = int(display_height * aspect_ratio)
        else:  # 縦長または正方形
            display_height = min(max_height, image_height)
            display_width = int(display_height * aspect_ratio)
            if display_width > max_width:
                display_width = max_width
                display_height = int(display_width / aspect_ratio)

        # ウィンドウサイズ調整（余白を極小化）
        window_width = display_width + 10   # 極小パディング
        window_height = display_height + 70  # ボタン領域を極小化
        self.resize(window_width, window_height)

        # 画像スケーリング
        scaled_pixmap = pixmap.scaled(
            display_width, display_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.image_label.setPixmap(scaled_pixmap)
        self.logger.info(f"表示サイズ: {display_width}x{display_height}, ウィンドウ: {window_width}x{window_height}")

        self.show()
        self.raise_()
        self.activateWindow()

    def update_zoom_info(self, scale_factor):
        """ズーム情報を更新"""
        zoom_percent = int(scale_factor * 100)
        self.zoom_label.setText(f"ズーム: {zoom_percent}% (Ctrl+マウスホイールで拡大縮小)")


class ImageTranslatorApp(QWidget):
    """メインアプリケーション"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('ImageTranslator.Main')
        self.clipboard = QApplication.clipboard()
        self.last_image = None
        self.last_image_hash = None
        self.result_window = ResultWindow()
        self.translation_thread = None
        self.config = app_config

        # 自動翻訳機能の状態（デフォルトOFF）
        self.auto_translation_enabled = False

        # 翻訳言語設定の初期化
        self.from_language = self.config.get('translation_settings', {}).get('from_language', 'japanese')
        self.to_language = self.config.get('translation_settings', {}).get('to_language', 'english')

        # システムトレイ初期化
        self.init_system_tray()

        # クリップボード監視タイマー
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_clipboard)
        check_interval = app_config['ui_settings']['clipboard_check_interval']
        self.timer.start(check_interval)

        self.logger.info("画像翻訳ツール起動 - クリップボード監視開始")

    def init_system_tray(self):
        """システムトレイ初期化"""
        self.logger.info("システムトレイ初期化")

        self.tray_icon = QSystemTrayIcon()

        # アイコンファイルを読み込み（assets/iconsフォルダから）
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets', 'icons')
        off_icon_path = os.path.join(assets_dir, 'OFF.png')

        if os.path.exists(off_icon_path):
            self.off_icon = QIcon(off_icon_path)
            self.logger.info(f"OFFアイコンを読み込みました: {off_icon_path}")
        else:
            # フォールバック用のアイコン
            self.logger.warning(f"OFFアイコンが見つかりません: {off_icon_path}")
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.gray)
            self.off_icon = QIcon(pixmap)

        on_icon_path = os.path.join(assets_dir, 'ON.png')
        if os.path.exists(on_icon_path):
            self.on_icon = QIcon(on_icon_path)
            self.logger.info(f"ONアイコンを読み込みました: {on_icon_path}")
        else:
            # フォールバック用のアイコン
            self.logger.warning(f"ONアイコンが見つかりません: {on_icon_path}")
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.green)
            self.on_icon = QIcon(pixmap)

        # 初期アイコンを設定（OFF状態）
        self.tray_icon.setIcon(self.off_icon)

        # トレイメニュー
        self.tray_menu = QMenu()
        self.create_tray_menu()
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.setToolTip("画像翻訳ツール - 自動翻訳: OFF")
        self.tray_icon.show()

        # 通知表示
        if self.tray_icon.isSystemTrayAvailable():
            self.tray_icon.showMessage(
                "画像翻訳ツール",
                "起動しました。自動翻訳はOFFです。システムトレイから有効にしてください。",
                QSystemTrayIcon.Information,
                2000
            )

    def create_tray_menu(self):
        """トレイメニューを作成（再構築可能）"""
        self.tray_menu.clear()

        # 自動翻訳ON/OFF切り替え機能
        self.translation_action = QAction("🔴 自動翻訳: OFF" if not self.auto_translation_enabled else "🟢 自動翻訳: ON", self)
        self.translation_action.triggered.connect(self.toggle_auto_translation)
        self.tray_menu.addAction(self.translation_action)

        self.tray_menu.addSeparator()

        # 翻訳設定サブメニュー
        translation_menu = self.tray_menu.addMenu("📝 翻訳設定")

        # FROM言語サブメニュー
        from_menu = translation_menu.addMenu("翻訳元言語 (From)")
        self.create_language_menu(from_menu, 'from')

        # TO言語サブメニュー
        to_menu = translation_menu.addMenu("翻訳先言語 (To)")
        self.create_language_menu(to_menu, 'to')

        # 現在の設定表示
        translation_menu.addSeparator()
        current_setting = translation_menu.addAction(
            f"現在: {LANGUAGE_MAP[self.from_language]['display']} → {LANGUAGE_MAP[self.to_language]['display']}"
        )
        current_setting.setEnabled(False)

        self.tray_menu.addSeparator()

        # テスト表示機能
        test_action = QAction("📸 画像表示テスト", self)
        test_action.triggered.connect(self.test_image_display)
        self.tray_menu.addAction(test_action)

        self.tray_menu.addSeparator()

        # 終了
        quit_action = QAction("終了", self)
        quit_action.triggered.connect(self.quit_app)
        self.tray_menu.addAction(quit_action)

    def create_language_menu(self, parent_menu, direction):
        """言語選択メニューを作成"""
        current_lang = self.from_language if direction == 'from' else self.to_language

        for lang_key, lang_info in LANGUAGE_MAP.items():
            # FROMとTOが同じ言語にならないようチェック
            if direction == 'from' and lang_key == self.to_language:
                action = QAction(f"  {lang_info['display']} (使用不可)", self)
                action.setEnabled(False)
            elif direction == 'to' and lang_key == self.from_language:
                action = QAction(f"  {lang_info['display']} (使用不可)", self)
                action.setEnabled(False)
            else:
                # 現在選択中の言語にチェックマーク
                if lang_key == current_lang:
                    action = QAction(f"✓ {lang_info['display']}", self)
                else:
                    action = QAction(f"  {lang_info['display']}", self)

                # ラムダ式を使ってクロージャを作成
                action.triggered.connect(lambda checked, l=lang_key, d=direction: self.change_language(l, d))

            parent_menu.addAction(action)

    def change_language(self, language_key, direction):
        """言語設定を変更"""
        if direction == 'from':
            self.from_language = language_key
            self.config['translation_settings']['from_language'] = language_key
        else:
            self.to_language = language_key
            self.config['translation_settings']['to_language'] = language_key

        # 設定ファイルを保存
        self.save_config()

        # メニューを再構築
        self.create_tray_menu()

        # 通知表示
        if self.tray_icon.isSystemTrayAvailable():
            self.tray_icon.showMessage(
                "翻訳設定変更",
                f"{LANGUAGE_MAP[self.from_language]['display']} → {LANGUAGE_MAP[self.to_language]['display']}",
                QSystemTrayIcon.Information,
                2000
            )

        self.logger.info(f"翻訳設定変更: {self.from_language} → {self.to_language}")

    def save_config(self):
        """設定をファイルに保存"""
        try:
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "config.json"

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)

            self.logger.info("設定ファイル保存完了")
        except Exception as e:
            self.logger.error(f"設定ファイル保存エラー: {str(e)}")

    def update_current_clipboard_hash(self):
        """現在のクリップボード画像のハッシュを更新（古い画像を処理しないため）"""
        try:
            mime_data = self.clipboard.mimeData()
            if mime_data.hasImage():
                qimage = self.clipboard.image()
                if not qimage.isNull():
                    # QImageをPIL Imageに変換してハッシュ計算
                    from PyQt5.QtCore import QByteArray, QBuffer, QIODevice

                    byte_array = QByteArray()
                    buffer = QBuffer(byte_array)
                    buffer.open(QIODevice.WriteOnly)
                    qimage.save(buffer, "PNG")

                    pil_buffer = BytesIO(byte_array.data())
                    pil_buffer.seek(0)

                    try:
                        pil_image = Image.open(pil_buffer)
                        import hashlib
                        image_hash = hashlib.md5(pil_image.tobytes()).hexdigest()
                        self.last_image_hash = image_hash
                        self.logger.info(f"現在のクリップボード画像ハッシュを更新: {image_hash[:8]}...")
                    except Exception as e:
                        self.logger.warning(f"クリップボード画像ハッシュ更新エラー: {str(e)}")
        except Exception as e:
            self.logger.warning(f"クリップボードハッシュ更新エラー: {str(e)}")

    def check_clipboard(self):
        """クリップボードをチェック"""
        # 自動翻訳が無効の場合は処理をスキップ
        if not self.auto_translation_enabled:
            return

        try:
            mime_data = self.clipboard.mimeData()

            if mime_data.hasImage():
                # QImageをPIL Imageに変換
                qimage = self.clipboard.image()

                if not qimage.isNull():
                    # QImageをQByteArrayに変換してからBytesIOに
                    from PyQt5.QtCore import QByteArray, QBuffer, QIODevice

                    byte_array = QByteArray()
                    buffer = QBuffer(byte_array)
                    buffer.open(QIODevice.WriteOnly)
                    qimage.save(buffer, "PNG")

                    # BytesIOに変換
                    pil_buffer = BytesIO(byte_array.data())
                    pil_buffer.seek(0)

                    # PIL Imageとして読み込み
                    try:
                        pil_image = Image.open(pil_buffer)

                        # 画像のハッシュ値を計算
                        import hashlib
                        image_hash = hashlib.md5(pil_image.tobytes()).hexdigest()

                        # 新しい画像の場合のみ処理
                        if self.last_image_hash != image_hash:
                            self.logger.info(f"新しい画像を検出: {pil_image.size}")
                            self.last_image_hash = image_hash
                            self.process_image(pil_image)

                    except Exception as e:
                        self.logger.error(f"画像変換エラー: {str(e)}", exc_info=True)

        except Exception as e:
            self.logger.error(f"クリップボードチェックエラー: {str(e)}", exc_info=True)

    def process_image(self, image):
        """画像を翻訳処理"""
        self.logger.info("翻訳処理を開始")

        # 通知
        if self.tray_icon.isSystemTrayAvailable():
            self.tray_icon.showMessage(
                "画像翻訳ツール",
                "翻訳処理を開始しました...",
                QSystemTrayIcon.Information,
                2000
            )

        # 翻訳スレッドが動作中の場合はキャンセル
        if self.translation_thread and self.translation_thread.isRunning():
            self.logger.warning("既に翻訳処理が実行中です")
            return

        # 翻訳スレッド開始
        self.translation_thread = TranslationThread(image, app_config, self.from_language, self.to_language)
        self.translation_thread.finished.connect(self.on_translation_finished)
        self.translation_thread.error.connect(self.on_translation_error)
        self.translation_thread.progress.connect(self.on_translation_progress)
        self.translation_thread.start()

    def on_translation_finished(self, translated_image):
        """翻訳完了時の処理"""
        self.logger.info("翻訳完了")

        # 生成画像を自動保存
        saved_path = self.save_translated_image(translated_image)

        # 結果表示
        self.result_window.show_image(translated_image)

        # 通知（保存パス情報も含める）
        if self.tray_icon.isSystemTrayAvailable():
            notification_duration = app_config['ui_settings']['notification_duration']
            self.tray_icon.showMessage(
                "画像翻訳ツール",
                f"翻訳が完了しました！\n保存先: {saved_path}",
                QSystemTrayIcon.Information,
                notification_duration
            )

    def save_translated_image(self, image):
        """翻訳された画像を一意の名前で自動保存"""
        try:
            # 設定から保存ディレクトリとファイル名フォーマットを取得
            save_dir = app_config['output_settings']['save_directory']
            filename_format = app_config['output_settings']['filename_format']

            # 保存フォルダ作成
            project_root = Path(__file__).parent.parent
            images_dir = project_root / save_dir
            images_dir.mkdir(parents=True, exist_ok=True)

            # 一意のファイル名生成（日時付き）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # ミリ秒まで
            filename = filename_format.format(timestamp=timestamp)
            filepath = images_dir / filename

            # 画像保存
            image.save(filepath, "PNG")
            self.logger.info(f"翻訳画像保存完了: {filepath}")

            return str(filepath)

        except Exception as e:
            self.logger.error(f"翻訳画像保存エラー: {str(e)}", exc_info=True)
            return "保存失敗"

    def on_translation_progress(self, message):
        """翻訳進捗通知の処理"""
        self.logger.info(f"進捗: {message}")

        # システムトレイ通知
        if self.tray_icon.isSystemTrayAvailable():
            self.tray_icon.showMessage(
                "翻訳処理中",
                message,
                QSystemTrayIcon.Information,
                2000
            )

    def on_translation_error(self, error_message):
        """翻訳エラー時の処理"""
        self.logger.error(f"翻訳エラー: {error_message}")

        # システムトレイ通知
        if self.tray_icon.isSystemTrayAvailable():
            self.tray_icon.showMessage(
                "翻訳エラー",
                f"エラーが発生しました:\n{error_message}",
                QSystemTrayIcon.Critical,
                5000
            )

        # エラーダイアログ表示
        QMessageBox.critical(None, "翻訳エラー", f"翻訳処理中にエラーが発生しました:\n\n{error_message}")

    def test_image_display(self):
        """画像表示テスト機能"""
        try:
            # imagesフォルダが存在するかチェック
            project_root = Path(__file__).parent.parent
            images_dir = project_root / "images"
            if not images_dir.exists():
                images_dir.mkdir(parents=True, exist_ok=True)

            # ファイル選択ダイアログを表示
            file_path, _ = QFileDialog.getOpenFileName(
                None,
                "テスト表示する画像を選択",
                str(images_dir),  # デフォルトディレクトリをimagesフォルダに設定
                "画像ファイル (*.png *.jpg *.jpeg *.bmp *.gif);;すべてのファイル (*)"
            )

            if file_path:
                # 選択された画像を読み込み
                try:
                    with Image.open(file_path) as img:
                        # RGB形式に変換（必要に応じて）
                        if img.mode != 'RGB':
                            img = img.convert('RGB')

                        # 画像表示ウィンドウを作成・表示
                        if not hasattr(self, 'result_window') or self.result_window is None:
                            self.result_window = ResultWindow()
                        self.result_window.show_image(img)

                        self.logger.info(f"🧪 テスト表示: {Path(file_path).name}")

                except Exception as e:
                    self.logger.error(f"画像読み込みエラー: {str(e)}")
                    QMessageBox.critical(None, "エラー", f"画像の読み込みに失敗しました:\n{str(e)}")
            else:
                self.logger.info("画像選択がキャンセルされました")

        except Exception as e:
            self.logger.error(f"テスト表示エラー: {str(e)}")
            QMessageBox.critical(None, "エラー", f"テスト表示に失敗しました:\n{str(e)}")

    def toggle_auto_translation(self):
        """自動翻訳機能のON/OFF切り替え"""
        self.auto_translation_enabled = not self.auto_translation_enabled

        if self.auto_translation_enabled:
            # ONの場合
            self.translation_action.setText("🟢 自動翻訳: ON")
            self.tray_icon.setToolTip("画像翻訳ツール - 自動翻訳: ON")
            # アイコンをON.pngに変更
            self.tray_icon.setIcon(self.on_icon)

            # 現在のクリップボード画像のハッシュを更新（古い画像を処理しないため）
            self.update_current_clipboard_hash()

            # 通知表示
            if self.tray_icon.isSystemTrayAvailable():
                notification_duration = app_config['ui_settings']['notification_duration']
                self.tray_icon.showMessage(
                    "画像翻訳ツール",
                    "自動翻訳が有効になりました。画像をクリップボードにコピーすると自動翻訳されます。",
                    QSystemTrayIcon.Information,
                    notification_duration
                )
            self.logger.info("自動翻訳機能: ON")
        else:
            # OFFの場合
            self.translation_action.setText("🔴 自動翻訳: OFF")
            self.tray_icon.setToolTip("画像翻訳ツール - 自動翻訳: OFF")
            # アイコンをOFF.pngに変更
            self.tray_icon.setIcon(self.off_icon)

            # 通知表示
            if self.tray_icon.isSystemTrayAvailable():
                notification_duration = app_config['ui_settings']['notification_duration']
                self.tray_icon.showMessage(
                    "画像翻訳ツール",
                    "自動翻訳が無効になりました。課金は発生しません。",
                    QSystemTrayIcon.Information,
                    notification_duration
                )
            self.logger.info("自動翻訳機能: OFF")

    def quit_app(self):
        """アプリケーション終了"""
        self.logger.info("アプリケーション終了")
        self.timer.stop()
        QApplication.quit()


def main():
    """メインエントリーポイント"""

    try:
        logger.info("=" * 50)
        logger.info("画像翻訳ツール起動")
        logger.info(f"Python: {sys.version}")
        logger.info(f"PyQt5: {PyQt5.QtCore.QT_VERSION_STR}")
        logger.info("=" * 50)

        # APIキーチェック
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEYが設定されていません")
            print("エラー: OPENAI_API_KEYが設定されていません")
            print(".envファイルに以下の形式で設定してください:")
            print("OPENAI_API_KEY=your-api-key-here")
            return
        else:
            logger.info(f"APIキー検出: {api_key[:10]}...")

        # アプリケーション初期化
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        # メインウィンドウ作成（非表示）
        translator = ImageTranslatorApp()

        # イベントループ開始
        logger.info("イベントループ開始")
        sys.exit(app.exec_())

    except Exception as e:
        logger.critical(f"起動エラー: {str(e)}", exc_info=True)
        print(f"エラーが発生しました。詳細はログファイルを確認してください。")
        print(f"エラー: {str(e)}")
        raise


if __name__ == "__main__":
    main()