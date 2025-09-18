from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFileDialog
from PyQt5.QtCore import pyqtSignal, Qt
from datetime import datetime
import sys
from qfluentwidgets import (PrimaryPushButton, ListWidget, TextEdit, FluentIcon as FIF,
                            StrongBodyLabel, TitleLabel,
                            StateToolTip,
                            SimpleCardWidget)

sys.path.append("..")
from QThread.Save_comment_Thread import SaveCommentThread
from QThread.Load_Settings import cfg


class CommentSaveTab(QWidget):
    """评论保存标签页 - 使用 Fluent 设计风格"""

    save_requested = pyqtSignal(list, dict, str)
    save_success = pyqtSignal(str)
    save_failed = pyqtSignal(str)
    save_warning = pyqtSignal()

    comment_selected = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.comments = []
        self.video_info = {}
        self.save_thread = None
        self.state_tooltip = None
        self.init_ui()

    def init_ui(self):
        """初始化结果界面布局"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 32, 20, 20)

        title_label = TitleLabel('评论结果')
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.stats_card = SimpleCardWidget()
        stats_layout = QVBoxLayout(self.stats_card)

        self.stats_label = StrongBodyLabel('共 0 条评论')
        self.stats_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self.stats_label)

        layout.addWidget(self.stats_card)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e0e0e0;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
        """)

        self.comments_list = ListWidget()
        self.comments_list.itemClicked.connect(self.on_comment_clicked)
        self.comments_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        splitter.addWidget(self.comments_list)


        self.comment_detail = TextEdit()
        self.comment_detail.setReadOnly(True)
        self.comment_detail.setMaximumHeight(300)

        self.comment_detail.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                padding: 8px;
            }
        """)
        splitter.addWidget(self.comment_detail)

        splitter.setSizes([400, 200])
        layout.addWidget(splitter)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.save_button = PrimaryPushButton('保存为JSON', self)
        self.save_button.setIcon(FIF.SAVE)
        self.save_button.clicked.connect(self.on_save_clicked)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def display_comments(self, comments, video_info):
        """显示评论数据"""
        self.comments = comments
        self.video_info = video_info
        self.comments_list.clear()
        self.comment_detail.clear()
        self.save_button.setEnabled(bool(comments))


        total_comments = len(comments)
        self.stats_label.setText(f'共 {total_comments} 条评论,此处不显示主评论')


        display_comments = comments[:500]

        for i, cmt in enumerate(display_comments):
            if cmt['parent'] != 0:
                continue
            member = cmt.get('member', {})
            content = cmt.get('content', {})
            username = member.get('uname', '未知用户')
            message = content.get('message', '')

            if len(message) > 50:
                message = message[:47] + '...'

            item_text = f"{i + 1}. {username}: {message}"
            self.comments_list.addItem(item_text)

    def on_comment_clicked(self, item):
        """评论点击事件处理"""
        index = self.comments_list.currentRow()
        if 0 <= index < len(self.comments):
            self.comment_selected.emit(index)
            self.show_comment_detail(index)

    def show_comment_detail(self, index):
        """显示评论详情"""
        cmt = self.comments[index]
        member = cmt.get('member', {})
        content = cmt.get('content', {})

        detail_text = f"""<b>用户名:</b> {member.get('uname', '未知用户')}
<b>用户ID:</b> {member.get('mid', '未知')}
<b>发布时间:</b> {datetime.fromtimestamp(cmt.get('ctime', 0)).strftime('%Y-%m-%d %H:%M:%S')}
<b>点赞数:</b> {cmt.get('like', 0)}
<b>IP地址:</b> {cmt.get('reply_control', {}).get('location', '未知')}
<b>性别:</b> {member.get('sex', '未知')}

<b>评论内容:</b>
{content.get('message', '')}
"""

        if 'replies' in cmt and cmt['replies']:
            detail_text += f"\n<b>子评论 ({len(cmt['replies'])} 条):</b>\n"
            for reply in cmt['replies']:
                reply_member = reply.get('member', {})
                reply_content = reply.get('content', {})
                detail_text += f"\n↳ <b>{reply_member.get('uname', '未知用户')}:</b> {reply_content.get('message', '')}\n"

        self.comment_detail.setHtml(detail_text)

    def on_save_clicked(self):
        """保存评论到JSON文件（使用线程）"""
        video_name = self.video_info.get('title', 'unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not self.comments:
            self.save_warning.emit()
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, '保存评论数据', f'{cfg.get(cfg.save_commentFolder)}/{video_name}_{timestamp}', 'JSON文件 (*.json)'
            )

        if filename:
            if not filename.endswith('.json'):
                filename += '.json'

            self.save_button.setEnabled(False)

            self.state_tooltip = StateToolTip('正在保存', '评论数据保存中...', self)
            self.state_tooltip.move(self.state_tooltip.getSuitablePos())
            self.state_tooltip.show()

            self.save_thread = SaveCommentThread(self.comments, self.video_info, filename)
            self.save_thread.save_progress.connect(self.update_save_progress)
            self.save_thread.save_finished.connect(self.on_save_finished)
            self.save_thread.save_error.connect(self.on_save_error)

            self.save_thread.start()

    def update_save_progress(self, current_step, total_steps, message):
        """更新保存进度"""
        if self.state_tooltip:
            progress = int((current_step / total_steps) * 100)
            self.state_tooltip.setTitle(f'正在保存 ({progress}%)')
            self.state_tooltip.setContent(message)

    def on_save_finished(self, filename, success):
        """保存完成处理"""
        if self.state_tooltip:
            self.state_tooltip.setState(True)
            self.state_tooltip = None

        self.save_button.setEnabled(True)

        if success:
            self.save_success.emit(filename)
        else:
            self.save_failed.emit('failed')

    def on_save_error(self, error_msg):
        """保存错误处理"""
        if self.state_tooltip:
            self.state_tooltip.setState(False)
            self.state_tooltip = None

        self.save_button.setEnabled(True)
        self.save_failed.emit(error_msg)

    def on_save_canceled(self):
        """用户取消保存"""
        if hasattr(self, 'save_thread'):
            self.save_thread.stop()
        self.save_button.setEnabled(True)
