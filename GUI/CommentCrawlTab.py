from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, Qt
import re
import sys
from bilibili_api import video, sync
from qfluentwidgets import (PrimaryPushButton, LineEdit, FluentIcon as FIF, StrongBodyLabel, BodyLabel, CaptionLabel,
                            TitleLabel, IndeterminateProgressRing, StateToolTip, CardWidget)

sys.path.append("..")
from QThread.Get_comment_Thread import CommentCrawlerThread



class CommentCrawlTab(QWidget):
    """评论爬取标签页 - 使用 Fluent 设计风格"""

    fetch_info_requested_warning = pyqtSignal()
    fetch_info_requested_success = pyqtSignal(str)
    fetch_info_requested_failed = pyqtSignal(str)

    crawl_comments_warning = pyqtSignal()
    crawl_comments_failed = pyqtSignal(list, int, dict, str)
    crawl_comments_finished = pyqtSignal(list, int, dict)

    def __init__(self):
        super().__init__()
        self.credential = None
        self.crawler_thread = None
        self.current_bv_id = None
        self.state_tooltip = None
        self.init_ui()

    def init_ui(self):
        """初始化爬虫界面布局"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 32, 20, 20)

        title_label = TitleLabel('评论爬取')
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        input_card = CardWidget()
        input_layout = QVBoxLayout(input_card)

        input_title = StrongBodyLabel('视频链接或BV号')
        input_layout.addWidget(input_title)

        bv_layout = QHBoxLayout()
        self.bv_input = LineEdit()
        self.bv_input.setPlaceholderText('请输入BV号或B站视频链接 (例如: BV1xx411x7xx)')
        self.bv_input.setClearButtonEnabled(True)
        bv_layout.addWidget(self.bv_input)

        input_layout.addLayout(bv_layout)
        layout.addWidget(input_card)

        self.info_card = CardWidget()
        info_layout = QVBoxLayout(self.info_card)

        info_title = StrongBodyLabel('视频信息')
        info_layout.addWidget(info_title)

        self.video_info_label = BodyLabel('未选择视频')
        self.video_info_label.setWordWrap(True)
        info_layout.addWidget(self.video_info_label)

        layout.addWidget(self.info_card)

        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(5)

        self.progress_ring = IndeterminateProgressRing()
        self.progress_ring.setVisible(False)
        progress_layout.addWidget(self.progress_ring, 0, Qt.AlignCenter)

        self.progress_label = CaptionLabel('')
        self.progress_label.setVisible(False)
        self.progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_label)

        layout.addLayout(progress_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.fetch_info_button = PrimaryPushButton('获取视频信息', self)
        self.fetch_info_button.setIcon(FIF.INFO)
        self.fetch_info_button.clicked.connect(self.fetch_video_info)
        self.fetch_info_button.setEnabled(False)
        button_layout.addWidget(self.fetch_info_button)

        self.crawl_button = PrimaryPushButton('开始爬取', self)
        self.crawl_button.setIcon(FIF.DOWNLOAD)
        self.crawl_button.clicked.connect(self.start_crawling)
        self.crawl_button.setEnabled(False)
        button_layout.addWidget(self.crawl_button)

        layout.addLayout(button_layout)
        layout.addStretch()

        self.setLayout(layout)

    def set_credential(self, credential):
        """设置登录凭证"""
        self.credential = credential
        self.fetch_info_button.setEnabled(True)

    def fetch_video_info(self):
        """获取视频信息"""
        bv_text = self.bv_input.text().strip()
        if not bv_text:
            self.fetch_info_requested_warning.emit()

            return

        bv_match = re.findall('BV.{10}', bv_text)
        if not bv_match:
            self.fetch_info_requested_warning.emit()
            return

        bv_id = bv_match[0]

        try:
            self.progress_ring.setVisible(True)
            self.progress_label.setText('正在获取视频信息...')
            self.progress_label.setVisible(True)
            self.fetch_info_button.setEnabled(False)

            v = video.Video(bvid=bv_id, credential=self.credential)
            video_info = sync(v.get_info())

            title = video_info.get('title', '未知标题')
            author = video_info.get('owner', {}).get('name', '未知作者')
            comment_count = video_info.get('stat', {}).get('reply', 0)

            self.video_info_label.setText(
                f'标题: {title}\n作者: {author}\n评论数: {comment_count}'
                )
            self.crawl_button.setEnabled(True)
            self.current_bv_id = bv_id
            self.fetch_info_requested_success.emit(bv_id)

            self.progress_ring.setVisible(False)
            self.progress_label.setVisible(False)
            self.fetch_info_button.setEnabled(True)


        except Exception as e:
            self.progress_ring.setVisible(False)
            self.progress_label.setVisible(False)
            self.fetch_info_button.setEnabled(True)
            self.fetch_info_requested_failed.emit(str(e))

    def start_crawling(self):
        """开始爬取评论"""
        if not self.current_bv_id:
            self.crawl_comments_warning.emit()
            return

        self.state_tooltip = StateToolTip('正在爬取', '评论数据爬取中...', self)
        self.state_tooltip.move(self.state_tooltip.getSuitablePos())
        self.state_tooltip.setVisible(True)
        self.state_tooltip.show()

        self.crawl_button.setEnabled(False)

        self.crawler_thread = CommentCrawlerThread(self.credential, self.current_bv_id)
        self.crawler_thread.progress_update.connect(self.update_progress)
        self.crawler_thread.finished.connect(self.on_crawl_finished)
        self.crawler_thread.error_occurred.connect(self.on_crawl_error)
        self.crawler_thread.start()

    def update_progress(self, current, total, message):
        """更新进度"""
        if self.state_tooltip:
            progress = int((current / total) * 100) if total > 0 else 0
            self.state_tooltip.setTitle(f'正在爬取 ({progress}%)')
            self.state_tooltip.setContent(message)

    def on_crawl_finished(self, comments, count, video_info):
        """爬取完成"""
        if self.state_tooltip:
            self.state_tooltip.setState(True)
            self.state_tooltip = None

        self.crawl_button.setEnabled(True)

        self.crawl_comments_finished.emit(comments, count, video_info)

    def on_crawl_error(self, comments, count, video_info, error_msg):
        """爬取错误"""
        if self.state_tooltip:
            self.state_tooltip.setState(False)
            self.state_tooltip.setVisible(False)
            self.state_tooltip = None

        self.crawl_button.setEnabled(True)
        self.crawl_comments_failed.emit(comments, count, video_info, str(error_msg))
