from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QPainterPath, QPixmap
from qfluentwidgets import BodyLabel, TitleLabel, CardWidget
import logging, requests
import os

logger = logging.getLogger(__name__)


class UserInfoPage(QWidget):
    """用户信息展示页"""

    logout_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.user_info = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = TitleLabel("用户信息")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.info_card = CardWidget()
        info_layout = QVBoxLayout(self.info_card)
        self.info_label = BodyLabel("未登录")
        self.info_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.info_label)
        layout.addWidget(self.info_card)

        self.avatar_label = QLabel("暂无头像")
        self.avatar_label.setFixedSize(100, 100)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet("""
            QLabel {
                border: 2px solid #f0f0f0;
                border-radius: 50px;
                background-color: #f0f0f0;
            }
        """)
        layout.addWidget(self.avatar_label, 0, Qt.AlignCenter)

        self.logout_btn = QPushButton("注销账户")
        self.logout_btn.setFixedWidth(120)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 6px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.logout_btn.clicked.connect(self.logout)
        layout.addWidget(self.logout_btn, 0, Qt.AlignCenter)

        layout.addStretch()

    def update_user_info(self, user_info):
        """更新用户信息"""
        self.user_info = user_info
        if not user_info:
            self.info_label.setText("未登录")
            self.avatar_label.setPixmap(QPixmap())
            self.avatar_label.setText("暂无头像")
            return

        name = user_info.get("name", "未知用户")
        user_id = user_info.get("mid", "未知ID")
        level = user_info.get("level", 0)
        vip_status = user_info.get("vip", {}).get("status", 0)

        info_text = f"""<b>{name}</b>
ID: {user_id}
等级: Lv{level}
{'🎖️ 大会员' if vip_status == 1 else '👤 普通用户'}
"""
        self.info_label.setText(info_text)

        avatar_url = user_info.get("face", "")
        if avatar_url:
            avatar_url = avatar_url.replace("http://", "https://")
            if "@" not in avatar_url:
                avatar_url += "@100w_100h_1c_1s.webp"
            self.load_avatar(avatar_url)

    def load_avatar(self, avatar_url):
        try:
            response = requests.get(avatar_url, timeout=10)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                circular_pixmap = self.create_circular_pixmap(pixmap, 100)
                self.avatar_label.setPixmap(circular_pixmap)
                self.avatar_label.setText("")
        except Exception as e:
            logger.error(f"加载头像失败: {e}")

    def create_circular_pixmap(self, pixmap, size):
        circular_pixmap = QPixmap(size, size)
        circular_pixmap.fill(Qt.transparent)
        painter = QPainter(circular_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        path = QPainterPath()
        path.addEllipse(QRectF(0, 0, size, size))
        painter.setClipPath(path)
        scaled_pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.end()
        return circular_pixmap

    def logout(self):
        """清空用户信息、删除本地凭证并触发注销信号"""
        self.user_info = None
        self.info_label.setText("未登录")
        self.avatar_label.setPixmap(QPixmap())
        self.avatar_label.setText("暂无头像")

        credential_path = os.path.join(os.path.dirname(__file__), "../config/credential.env")
        if os.path.exists(credential_path):
            try:
                os.remove(credential_path)
                logger.info("已删除本地登录凭证文件")
            except Exception as e:
                logger.error(f"删除凭证文件失败: {e}")

        self.logout_signal.emit()
