from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,QFileDialog, QPushButton,
    QFrame, QHBoxLayout, QGraphicsDropShadowEffect,QProgressBar
    )
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QColor
import matplotlib.pyplot as plt
import pandas as pd
import io
from QThread.Data_analysis_Thread import AnalysisThread


plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


# ------------------ 把matplotlib图表转成QLabel ------------------
def fig_to_label(fig, width=500, height=300):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)

    pixmap = QPixmap()
    ok = pixmap.loadFromData(buf.getvalue())
    buf.close()

    if not ok:
        label = QLabel("图表渲染失败")
        return label

    label = QLabel()
    label.setPixmap(pixmap)
    label.setScaledContents(True)
    label.setMinimumSize(width, height)
    label.setAlignment(Qt.AlignCenter)

    plt.close(fig)
    return label


# ------------------ Fluent卡片封装 ------------------
def create_card(title, widget):
    card = QFrame()
    card.setFrameShape(QFrame.StyledPanel)
    card.setStyleSheet("""
        QFrame {
            background-color: #FFFFFF;
            border-radius: 14px;
            border: 0.2px solid #E1E1E1;
        }
    """)
    layout = QVBoxLayout(card)
    label_title = QLabel(title)
    label_title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
    label_title.setAlignment(Qt.AlignCenter)
    layout.addWidget(label_title)
    layout.addWidget(widget)
    layout.setContentsMargins(0, 0, 0, 0)

    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(12)
    shadow.setOffset(0, 4)
    shadow.setColor(QColor(150, 150, 150, 100))
    card.setGraphicsEffect(shadow)

    return card


# ------------------ GUI 标签页 ------------------

class CommentAnalysisTab(QWidget):
    analysis_success = pyqtSignal()
    def __init__(self):
        super().__init__()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        main_layout.setContentsMargins(0, 32, 0, 0)
        self.container = QWidget()
        self.vbox_layout = QVBoxLayout(self.container)
        self.vbox_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.container)

        # ---------- 状态栏（工具提示 + 进度条） ----------
        self.label_status = QLabel("请加载 JSON 文件")
        self.label_status.setAlignment(Qt.AlignCenter)
        self.vbox_layout.addWidget(self.label_status)

        # QProgressBar 用于显示进度
        # 在 CommentAnalysisTab.__init__ 中加入进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.vbox_layout.addWidget(self.progress_bar)



        # 按钮
        self.btn_load = QPushButton("选择本地 JSON 文件")
        self.btn_load.setFixedHeight(40)
        self.btn_load.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                color: white;
                background-color: #0078D4;
                border: 2px solid #005A9E;
                border-radius: 8px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #005A9E;
                border-color: #004578;
            }
            QPushButton:pressed {
                background-color: #004578;
                border-color: #003366;
            }
        """)
        self.btn_load.clicked.connect(self.load_local_file)
        self.vbox_layout.addWidget(self.btn_load)

        self.thread = None

    # ------------------ 分析线程进度更新 ------------------
    # 回调更新进度
    def on_progress(self, current, total, msg):
        self.label_status.setText(f"{msg} {current}/{total}")
        self.progress_bar.setValue(int(current / total * 100))

    def on_failed(self, err):
        self.label_status.setText(f"分析失败：{err}")
        self.progress_bar.setValue(0)

    # ------------------ 点击按钮读取本地文件 ------------------
    def load_local_file(self):
        self.progress_bar.setVisible(True)
        self.label_status.setVisible(True)
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 JSON 文件", "", "JSON Files (*.json)"
        )
        if file_path:
            self.start_analysis(file_path)

    # ------------------ 启动分析线程 ------------------
    def start_analysis(self, file_path):
        self.label_status.setText(f"分析中：{file_path}")
        # 在 CommentAnalysisTab 里
        self.thread = AnalysisThread(file_path)
        self.thread.progress.connect(self.on_progress)
        self.thread.finished.connect(self.on_finished)
        self.thread.failed.connect(self.on_failed)
        self.thread.start()


    # ------------------ 图表封装 ------------------
    def plot_donut(self, data_dict, title):
        fig, ax = plt.subplots(figsize=(5, 5))
        labels, sizes = list(data_dict.keys()), list(data_dict.values())
        ax.pie(sizes, labels=labels, autopct='%1.1f%%',
               startangle=90, pctdistance=0.75)
        ax.set_title(title, fontdict={'fontsize': 14, 'fontweight': 'bold'})
        return fig_to_label(fig, 400, 300)

    def plot_line(self, data_dict, title, xlabel, ylabel):
        fig, ax = plt.subplots(figsize=(8, 4))
        s = pd.Series(data_dict)
        s.index = pd.to_datetime(s.index)
        idx = pd.date_range(s.index.min(), s.index.max())
        s = s.reindex(idx, fill_value=0)
        ax.plot(s.index, s.values, marker='o', linestyle='-', color='skyblue')
        ax.set_title(title, fontdict={'fontsize': 14, 'fontweight': 'bold'})
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        fig.autofmt_xdate(rotation=45)
        fig.tight_layout()
        return fig_to_label(fig, 500, 300)

    def plot_bar(self, data_dict, title, xlabel, ylabel):
        fig, ax = plt.subplots(figsize=(8, 4))
        keys, values = list(data_dict.keys()), list(data_dict.values())
        ax.bar(keys, values, color='steelblue')
        ax.set_title(title, fontdict={'fontsize': 14, 'fontweight': 'bold'})
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        fig.tight_layout()
        return fig_to_label(fig, 500, 300)

    def add_wordcloud_row(self, wc1_path, wc2_path, title1="全部评论", title2="高赞评论"):
        container = QWidget()
        hbox = QHBoxLayout(container)
        # 第一个词云
        vbox1 = QVBoxLayout()
        label1_title = QLabel(title1)
        label1_title.setAlignment(Qt.AlignCenter)
        vbox1.addWidget(label1_title)
        label1_img = QLabel()
        pixmap1 = QPixmap(wc1_path)
        label1_img.setPixmap(pixmap1.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        label1_img.setAlignment(Qt.AlignCenter)
        vbox1.addWidget(label1_img)
        hbox.addLayout(vbox1)

        # 第二个词云
        vbox2 = QVBoxLayout()
        label2_title = QLabel(title2)
        label2_title.setAlignment(Qt.AlignCenter)
        vbox2.addWidget(label2_title)
        label2_img = QLabel()
        pixmap2 = QPixmap(wc2_path)
        label2_img.setPixmap(pixmap2.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        label2_img.setAlignment(Qt.AlignCenter)
        vbox2.addWidget(label2_img)
        hbox.addLayout(vbox2)

        return container
    def add_high_like_comments(self, df, top_n=5):
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.addWidget(QLabel(f"前 {top_n} 条高赞评论示例"))
        top_comments = df.sort_values(by='like', ascending=False).head(top_n)
        for idx, row in top_comments.iterrows():
            label = QLabel(f"【{row['like']} 赞】 {row['message']}")
            label.setWordWrap(True)
            vbox.addWidget(label)
        return container

    def add_sentiment_examples(self, df, n=2):
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.addWidget(QLabel("情感示例"))
        for sentiment in ['正面', '负面']:
            vbox.addWidget(QLabel(f"{sentiment}示例："))
            samples = df[df['sentiment_label'] == sentiment].head(n)
            for idx, row in samples.iterrows():
                label = QLabel(f"【{row['like']} 赞】 {row['message']}")
                label.setWordWrap(True)
                vbox.addWidget(label)
        return container


    # ------------------ 分析完成 ------------------
    def on_finished(self, result):
        df = result['df']

        self.label_status.setVisible(False)
        self.progress_bar.setVisible(False)
        for i in reversed(range(self.vbox_layout.count())):
            widget = self.vbox_layout.itemAt(i).widget()
            if widget and widget != self.btn_load and widget!=self.progress_bar and widget !=self.label_status:  # 保留加载文件按钮
                widget.deleteLater()

        self.vbox_layout.addWidget(
            create_card("情感分析", self.plot_donut(result['sentiment'], "情感分析"))
            )
        self.vbox_layout.addWidget(
            create_card("情感示例", self.add_sentiment_examples(df))
            )
        self.vbox_layout.addWidget(
            create_card("每日评论热度", self.plot_line(result['daily_counts'], "每日评论热度", "日期", "评论数"))
            )
        self.vbox_layout.addWidget(
            create_card("高赞评论", self.add_high_like_comments(df))
            )
        self.vbox_layout.addWidget(
            create_card("词云展示", self.add_wordcloud_row(result['wordcloud_all'], result['wordcloud_high']))
            )

        self.vbox_layout.addWidget(self.btn_load)

        self.label_status.setText("分析完成 ✅")
        self.analysis_success.emit()


