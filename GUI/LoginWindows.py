import os
import json
import requests
from datetime import datetime
import logging
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QWidget

from bilibili_api import user, Credential, sync
from qfluentwidgets import (
    PrimaryPushButton, FluentIcon as FIF,
    TitleLabel, CardWidget, AvatarWidget, setThemeColor, setTheme, Theme,
    IndeterminateProgressRing
    )
from QThread.Login_Thread import QrLoginThread
from QThread.Login_with_credential_Thread import LoginWithCredentialQThread

logger = logging.getLogger(__name__)


class LoginWindow(QDialog):
    """登录小窗口 - Fluent 设计"""
    login_success = pyqtSignal(object, object)
    login_failed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.login_thread = None
        self.credential = None
        self.user_info = None

        setTheme(Theme.LIGHT)
        setThemeColor('#00a1d6')

        self.config_dir = 'config'
        self.credential_file = os.path.join(self.config_dir, 'credential.env')

        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon = os.path.join(self.script_dir, '../resource/icon/256.png')
        self.setWindowIcon(QIcon(self.icon))
        self.setWindowTitle("EchoBi——B站评论爬虫工具")
        self.setFixedSize(350, 550)
        self.setWindowModality(Qt.ApplicationModal)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title_layout = QVBoxLayout()
        icon_label = QLabel()
        icon_pixmap = QPixmap(self.icon).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignCenter)

        title_label = TitleLabel('EchoBi')
        title_label.setAlignment(Qt.AlignCenter)

        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        layout.addLayout(title_layout)

        self.avatar_show = False

        self.avatar_card = CardWidget(self)
        avatar_layout = QVBoxLayout(self.avatar_card)
        self.qr_code_widget = QWidget(self)
        self.qr_code_widget.setFixedSize(170, 170)
        self.qr_layout = QVBoxLayout(self.qr_code_widget)
        self.qr_label = QLabel("扫码登录B站账号", self)
        self.qr_layout.addWidget(self.qr_label)
        self.qr_code_widget.setVisible(True)
        avatar_layout.addWidget(self.qr_code_widget, alignment=Qt.AlignCenter)
        if os.path.exists(self.credential_file):
            try:
                self.qr_label.setVisible(False)
                with open(self.credential_file, 'r', encoding='utf-8') as f:
                    credential_data = json.load(f)
                credential = Credential(
                    sessdata=credential_data.get('sessdata'),
                    bili_jct=credential_data.get('bili_jct'),
                    buvid3=credential_data.get('buvid3', ''),
                    dedeuserid=credential_data.get('DedeUserid', ''),
                    ac_time_value=credential_data.get('ac_time_value', ''),
                    buvid4=credential_data.get('buvid4', '')
                    )
                self.qr_code_widget.setVisible(False)
                self.avatar_widget = AvatarWidget(self)
                self.avatar_widget.setFixedSize(100, 100)
                sync(self.get_user_avatar(credential))
                self.avatar_show = True
                avatar_layout.addWidget(self.avatar_widget, alignment=Qt.AlignCenter)
                self.avatar_label = QLabel("点击头像进行快速登录", self)
                avatar_layout.addWidget(self.avatar_label, alignment=Qt.AlignCenter)
                self.avatar_widget.mousePressEvent = self.on_avatar_click
            except:
                return
        layout.addWidget(self.avatar_card)

        self.other_account_button = PrimaryPushButton('其他账号', self)
        if not self.avatar_show:
            self.other_account_button.setText("点击刷新二维码")
        self.other_account_button.setIcon(FIF.QRCODE)
        self.other_account_button.clicked.connect(self.start_qr_login)

        layout.addWidget(self.other_account_button)

        self.progress_ring = IndeterminateProgressRing()
        self.progress_ring.setVisible(False)
        layout.addWidget(self.progress_ring, alignment=Qt.AlignCenter)

    async def get_user_avatar(self, credential):
        """通过 Bilibili API 获取用户头像并显示"""
        try:
            User = user.User(int(credential.dedeuserid), credential=credential)
            user_info = await User.get_user_info()
            response = requests.get(user_info.get('face', ""))
            if response.status_code == 200:
                avatar_image = QImage.fromData(response.content)
                self.avatar_pixmap = QPixmap.fromImage(avatar_image)
                self.avatar_widget.setPixmap(self.avatar_pixmap.scaled(100, 100, Qt.KeepAspectRatio))
            else:
                logger.error("头像下载失败")
        except Exception as e:
            logger.error(f"获取头像失败: {e}")

    def on_avatar_click(self, event):
        """头像点击触发快速登录"""
        self.login_with_avatar()

    def login_with_avatar(self):
        """点击头像进行快速登录"""
        logger.info("快速登录")
        self.login_with_saved_credential()

    def start_qr_login(self):
        """点击‘其他账号’按钮生成二维码"""
        self.progress_ring.setVisible(True)
        self.progress_ring.setBaseSize(60, 60)
        self.other_account_button.setEnabled(False)
        if self.avatar_show:
            self.avatar_widget.setVisible(False)
            self.avatar_label.setVisible(False)
        self.login_thread = QrLoginThread(self)
        self.login_thread.qr_ready.connect(self.update_qr)
        self.login_thread.login_success.connect(self.on_login_success)
        self.login_thread.login_failed.connect(self.on_login_failed)
        self.login_thread.start()

    def update_qr(self, qr_path: str):
        """更新二维码图片"""
        pixmap = QPixmap(qr_path).scaled(
            self.qr_code_widget.width() - 10,
            self.qr_code_widget.height() - 10,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
            )
        self.qr_code_widget.setVisible(True)
        self.qr_label.setPixmap(pixmap)
        self.qr_label.setText("")

    def login_with_saved_credential(self):
        try:
            self.login_with_saved_credential_thread = LoginWithCredentialQThread()
            self.login_with_saved_credential_thread.login_with_saved_credential_success.connect(self.on_login_success)
            self.login_with_saved_credential_thread.login_with_saved_credential_failed.connect(
                self.on_auto_login_failed)
            self.login_with_saved_credential_thread.start()
        except Exception as e:
            logger.error(f'自动登录失败: {e}')
            return False

    def on_auto_login_failed(self, error_msg):
        logger.info(f'自动登录失败: {error_msg}')

    def on_login_success(self, credential, user_info):
        """登录成功后处理"""
        self.progress_ring.setVisible(False)
        self.other_account_button.setEnabled(True)

        self.credential = credential
        self.user_info = user_info

        self.save_credential(credential)

        self.login_success.emit(credential, user_info)
        self.accept()

    def on_login_failed(self, error_msg):
        """登录失败后处理"""
        self.progress_ring.setVisible(False)
        self.other_account_button.setEnabled(True)
        self.login_failed.emit(error_msg)

    def save_credential(self, credential):
        """保存凭证"""
        try:
            credential_data = {
                'sessdata': credential.sessdata,
                'bili_jct': credential.bili_jct,
                'buvid3': getattr(credential, 'buvid3', ''),
                'buvid4': getattr(credential, 'buvid4', ''),
                'DedeUserid': getattr(credential, 'dedeuserid', ''),
                'ac_time_value': getattr(credential, 'ac_time_value', ''),
                'save_time': datetime.now().isoformat()
                }

            os.makedirs(self.config_dir, exist_ok=True)

            with open(self.credential_file, 'w', encoding='utf-8') as f:
                json.dump(credential_data, f, ensure_ascii=False, indent=2)

            logger.info("登录凭证已保存")
        except Exception as e:
            logger.error(f"保存凭证失败: {e}")
