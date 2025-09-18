from PyQt5.QtCore import QSize, Qt, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QStackedWidget, QHBoxLayout, QDialog, QLabel, QGraphicsOpacityEffect
import sys
import os, logging
from qfluentwidgets import setThemeColor, InfoBar, InfoBarPosition, FluentIcon as FIF
from qfluentwidgets import (NavigationInterface, NavigationItemPosition, MessageBox,
                            setTheme, Theme, qrouter)
from qframelesswindow import FramelessWindow, TitleBar

from .CommentCrawlTab import CommentCrawlTab
from .CommentSaveTab import CommentSaveTab
from .LoginWindows import LoginWindow
from .UserInfoPage import UserInfoPage
from .CommentAnalysisTab import CommentAnalysisTab
from .SettingsTab import SettingsTab

sys.path.append("..")
from QThread.Audio_Thread import AudioThread

logger = logging.getLogger(__name__)

class CustomTitleBar(TitleBar):
    """ 自定义标题栏 - 包含图标和标题 """

    def __init__(self, parent):
        super().__init__(parent)
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(22, 22)
        self.hBoxLayout.insertSpacing(0, 43)
        self.hBoxLayout.insertWidget(1, self.iconLabel, 0, Qt.AlignLeft | Qt.AlignBottom)
        self.window().windowIconChanged.connect(self.setIcon)

        self.titleLabel = QLabel(self)
        self.hBoxLayout.insertWidget(2, self.titleLabel, 0, Qt.AlignLeft | Qt.AlignBottom)
        self.titleLabel.setObjectName('titleLabel')
        self.window().windowTitleChanged.connect(self.setTitle)

    def setTitle(self, title):
        """设置标题文字"""
        self.titleLabel.setText(title)
        self.titleLabel.setStyleSheet("font: 9pt '微软雅黑';")
        self.titleLabel.adjustSize()

    def setIcon(self, icon):
        """设置图标"""
        self.iconLabel.setPixmap(QIcon(icon).pixmap(22, 22))

class BilibiliCommentGUI(FramelessWindow):
    """B站评论爬虫工具主窗口 - 使用Fluent设计"""

    def __init__(self):
        super().__init__()

        self.setTitleBar(CustomTitleBar(self))
        self.hBoxLayout = QHBoxLayout(self)

        self.stackWidget = QStackedWidget(self)

        self.navigationInterface = NavigationInterface(
            self, showMenuButton=True, showReturnButton=True)

        self.audio_thread = AudioThread()
        self.init_ui()

    def initWindow(self):
        """初始化窗口"""
        self.resize(900, 750)

        setTheme(Theme.LIGHT)
        setThemeColor('#00a1d6')
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon = os.path.join(script_dir, '../resource/icon/256.png')
        self.setWindowIcon(QIcon(icon))
        self.setWindowTitle('EchoBi——B站评论爬虫工具')

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def init_ui(self):
        """初始化用户界面"""

        # === 弹出登录窗口 ===
        login_win = LoginWindow(self)
        if login_win.exec_() != QDialog.Accepted:
            self.close()
            return

        self.crawl_tab = CommentCrawlTab()
        self.save_tab = CommentSaveTab()
        self.user_info_page = UserInfoPage()
        self.analysis_tab = CommentAnalysisTab()
        self.settings_tab = SettingsTab()

        self.crawl_tab.setObjectName('crawl')
        self.save_tab.setObjectName('save')
        self.analysis_tab.setObjectName('analysis')
        self.settings_tab.setObjectName('settings')

        self.on_login_success(login_win.credential, login_win.user_info)

        self.initLayout()
        self.initNavigation()
        self.initWindow()

        self.stackWidget.setCurrentWidget(self.crawl_tab)
        self.navigationInterface.setCurrentItem('crawl')

        self.connect_signals()

    def initNavigation(self):
        self.addSubInterface(self.crawl_tab, FIF.DOWNLOAD, '爬取')
        self.addSubInterface(self.save_tab, FIF.DOCUMENT, '结果')
        self.addSubInterface(self.analysis_tab, FIF.CHAT, '分析')

        if self.user_info:
            avatar_icon = self.get_user_avatar_icon(self.user_info.get("face", ""))
            self.addSubInterface(self.user_info_page, avatar_icon, self.user_info.get("name", "用户"),
                                 position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settings_tab, FIF.SETTING, '设置',
                             position=NavigationItemPosition.BOTTOM)
        self.navigationInterface.setBaseSize(QSize(48, 48))
        self.navigationInterface.addSeparator()
        self.navigationInterface.setExpandWidth(300)
        self.stackWidget.currentChanged.connect(self.onCurrentInterfaceChanged)

    def get_user_avatar_icon(self, avatar_url: str):
        """将用户头像转为 QIcon 用于导航"""
        try:
            import requests
            response = requests.get(avatar_url, timeout=10)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                circular_pixmap = self.user_info_page.create_circular_pixmap(pixmap, 48)
                return QIcon(circular_pixmap)
        except Exception as e:
            logger.error(f"头像加载失败: {e}")
        return FIF.PEOPLE.icon()

    def initLayout(self):
        """初始化主布局"""
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addWidget(self.stackWidget)
        self.hBoxLayout.setStretchFactor(self.stackWidget, 1)

        self.titleBar.raise_()
        self.navigationInterface.displayModeChanged.connect(self.titleBar.raise_)

    def switchTo(self, widget):
        self.stackWidget.setCurrentWidget(widget)

    def onCurrentInterfaceChanged(self, index):
        widget = self.stackWidget.widget(index)

        w = self.stackWidget.width()
        h = self.stackWidget.height()

        widget.setGeometry(0, h, w, h)

        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0.0)

        anim_slide = QPropertyAnimation(widget, b"geometry", self)
        anim_slide.setDuration(300)
        anim_slide.setStartValue(QRect(0, h, w, h))
        anim_slide.setEndValue(QRect(0, 0, w, h))
        anim_slide.setEasingCurve(QEasingCurve.OutCubic)

        anim_fade = QPropertyAnimation(opacity_effect, b"opacity", self)
        anim_fade.setDuration(400)
        anim_fade.setStartValue(0.0)
        anim_fade.setEndValue(1.0)
        anim_fade.setEasingCurve(QEasingCurve.InOutQuad)

        self.anim = [anim_slide, anim_fade]

        anim_slide.start()
        anim_fade.start()

        self.navigationInterface.setCurrentItem(widget.objectName())
        qrouter.push(self.stackWidget, widget.objectName())

    def addSubInterface(self, interface, icon, text: str, position=NavigationItemPosition.TOP):
        """添加子界面到导航栏"""
        self.stackWidget.addWidget(interface)
        self.navigationInterface.addItem(
            routeKey=interface.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface),
            position=position,
            tooltip=text
            )

    def connect_signals(self):
        """连接所有信号槽"""
        try:
            self.crawl_tab.crawl_comments_finished.connect(self.set_comments_data)
            self.crawl_tab.crawl_comments_warning.connect(self.crawl_comments_warning)
            self.crawl_tab.crawl_comments_failed.connect(self.crawl_comments_failed)
            self.crawl_tab.fetch_info_requested_failed.connect(self.fetch_info_requested_failed)
            self.crawl_tab.fetch_info_requested_success.connect(self.fetch_info_requested_success)
            self.crawl_tab.fetch_info_requested_warning.connect(self.fetch_info_requested_warning)

            self.save_tab.save_warning.connect(self.save_warning)
            self.save_tab.save_success.connect(self.save_success)
            self.save_tab.save_failed.connect(self.save_failed)

            self.user_info_page.logout_signal.connect(self.handle_logout)

            self.analysis_tab.analysis_success.connect(self.analysis_success)

            self.settings_tab.about_us_signal.connect(self.show_about_us)


        except Exception as e:
            InfoBar.warning(
                title='连接信号错误',
                content=f'连接信号错误{e}',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000,
                parent=self
                )
            self.audio_thread.play_warning()

    def on_login_success(self, credential, user_info):
        """登录成功处理"""
        try:
            self.user_credential = credential
            self.user_info = user_info
            self.crawl_tab.set_credential(credential)
            self.user_info_page.update_user_info(self.user_info)
            InfoBar.success(
                title='登录成功',
                content=f'欢迎回来，{user_info.get("name", "用户")}！',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000,
                parent=self
                )
            self.audio_thread.play_success()
        except Exception as e:
            print(f"登录成功处理错误: {e}")

    def on_login_failed(self, error_msg):
        """登录失败处理"""

        InfoBar.error(
            title='登录失败',
            content=error_msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=6000,
            parent=self
            )
        self.audio_thread.play_error()

    def fetch_info_requested_warning(self):
        """未输入bv号"""
        InfoBar.warning(
            title='输入错误',
            content='未找到有效的BV号',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=6000,
            parent=self
            )
        self.audio_thread.play_warning()

    def fetch_info_requested_success(self, bv_id):
        """查询到视频信息"""
        InfoBar.success(
            title='获取成功',
            content=f'{bv_id}视频信息获取完成',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=4000,
            parent=self
            )
        self.audio_thread.play_success()

    def fetch_info_requested_failed(self, error):
        """获取视频信息失败"""
        InfoBar.error(
            title='获取失败',
            content=f'获取视频信息失败: {str(error)}',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=8000,
            parent=self
            )

    def crawl_comments_warning(self):
        '''爬取评论警告'''
        InfoBar.warning(
            title='操作错误',
            content='请先获取视频信息',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=6000,
            parent=self
            )
        self.audio_thread.play_warning()

    def crawl_comments_failed(self, comments, count, video_info, error):
        '''爬取失败'''
        if '412' in error:
            InfoBar.error(
                title='爬取错误',
                content=f'触发反爬机制，请降低请求频率或稍后再试,已爬取{count}条评论',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=8000,
                parent=self
                )
        else:
            InfoBar.error(
                title='爬取错误',
                content=f'出现错误{error},已爬取{count}条评论',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=8000,
                parent=self
                )
        if len(comments) != 0:
            self.save_tab.display_comments(comments, video_info)
        self.audio_thread.play_error()

    def handle_logout(self):
        InfoBar.error(
            title='登出',
            content=f'成功登出',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=4000,
            parent=self
            )
        """用户注销后的处理逻辑"""
        self.user_credential = None
        self.stackWidget.setCurrentWidget(self.crawl_tab)
        login_win = LoginWindow(self)
        if login_win.exec_() == QDialog.Accepted:
            self.user_credential = login_win.credential
            self.user_info = login_win.user_info
            self.user_info_page.update_user_info(self.user_info)
            self.on_login_success(login_win.credential, login_win.user_info)
        else:
            self.close()

    def set_comments_data(self, comments, count, video_info):
        """设置评论数据"""
        try:
            self.save_tab.display_comments(comments, video_info)
            InfoBar.success(
                title='爬取完成',
                content=f'共获取 {count} 条评论',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000,
                parent=self
                )
            self.audio_thread.play_success()
        except Exception as e:
            print(f"设置评论数据错误: {e}")

    def save_warning(self):
        """保存评论警告"""
        InfoBar.warning(
            title='警告',
            content='没有评论数据可保存',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=6000,
            parent=self
            )
        self.audio_thread.play_warning()

    def save_success(self, filename):
        """成功保存评论"""
        InfoBar.success(
            title='保存成功',
            content=f'评论数据已保存到: {filename}',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=6000,
            parent=self
            )
        self.audio_thread.play_success()

    def save_failed(self, error):
        """保存评论失败"""
        InfoBar.error(
            title='保存错误',
            content=f'保存过程中出现错误: {error}',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=8000,
            parent=self
            )
        self.audio_thread.play_error()

    def analysis_success(self):
        InfoBar.success(
            title='分析成功',
            content=f'分析成功',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=6000,
            parent=self
            )
        self.audio_thread.play_success()

    def show_about_us(self):
        """显示关于我们窗口"""
        w = MessageBox(
            "关于我们",
            "作者：雀玖r\n"
            "联系方式：sxu79r@163.com\n"
            "当前版本:v1.0\n"
            "感谢您的使用！", self
            )
        w.exec()
