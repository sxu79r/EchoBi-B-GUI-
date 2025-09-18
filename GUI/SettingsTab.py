from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QInputDialog, QSlider
from qfluentwidgets import (
    ScrollArea, SettingCardGroup, PushSettingCard, RangeSettingCard, InfoBar, InfoBarPosition, HyperlinkCard,
    OptionsSettingCard, PrimaryPushSettingCard, FluentIcon as FIF,
    )
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QStandardPaths
from PyQt5.QtGui import QDesktopServices

from QThread.Audio_Thread import AudioThread
from QThread.Load_Settings import cfg


class MyRangeSettingCard(RangeSettingCard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        slider = self.findChild(QSlider)
        self.audio_thread = AudioThread()
        if slider:
            slider.valueChanged.connect(lambda val: self.setContent(str(val)))
            slider.sliderReleased.connect(self.onRelease)

    releaseChanged = pyqtSignal(int)

    def onRelease(self):
        slider = self.findChild(QSlider)
        val = slider.value()
        self.releaseChanged.emit(val)


class SettingsTab(ScrollArea):
    """ 设置标签页界面 """
    about_us_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.scrollWidget = QWidget()
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.vbox = QVBoxLayout(self.scrollWidget)
        self.setViewportMargins(10, 32, 10, 20)
        self.vbox.setContentsMargins(20, 0, 20, 20)

        self.__initCrawlSettings()
        self.__initAudioSettings()
        self.__initUpdateSettings()

    # -----------------------------
    # 爬虫相关设置
    # -----------------------------
    def __initCrawlSettings(self):
        crawlGroup = SettingCardGroup("爬虫设置", self.scrollWidget)

        self.commentFolderCard = PushSettingCard(
            "评论保存目录",
            FIF.FOLDER,
            "当前路径",
            cfg.get(cfg.save_commentFolder),
            parent=crawlGroup
            )
        self.commentFolderCard.clicked.connect(self.__onCommentFolderClicked)

        self.mainLowerCard = PushSettingCard(
            "主评论下限",
            FIF.HISTORY,
            "当前值",
            str(cfg.get(cfg.main_comment_time_lowerlimit)),
            parent=crawlGroup
            )
        self.mainLowerCard.clicked.connect(lambda: self.__onFloatValueClicked(
            self.mainLowerCard, cfg.main_comment_time_lowerlimit, "主评论下限", 0.5, 3.0, 0.1
            ))

        self.mainUpperCard = PushSettingCard(
            "主评论上限",
            FIF.HISTORY,
            "当前值",
            str(cfg.get(cfg.main_comment_time_upperlimit)),
            parent=crawlGroup
            )
        self.mainUpperCard.clicked.connect(lambda: self.__onFloatValueClicked(
            self.mainUpperCard, cfg.main_comment_time_upperlimit, "主评论上限", 1.0, 5.0, 0.1
            ))

        self.subLowerCard = PushSettingCard(
            "子评论下限",
            FIF.HISTORY,
            "当前值",
            str(cfg.get(cfg.sub_comment_time_lowerlimit)),
            parent=crawlGroup
            )
        self.subLowerCard.clicked.connect(lambda: self.__onFloatValueClicked(
            self.subLowerCard, cfg.sub_comment_time_lowerlimit, "子评论下限", 0.5, 3.0, 0.1
            ))

        self.subUpperCard = PushSettingCard(
            "子评论上限",
            FIF.HISTORY,
            "当前值",
            str(cfg.get(cfg.sub_comment_time_upperlimit)),
            parent=crawlGroup
            )
        self.subUpperCard.clicked.connect(lambda: self.__onFloatValueClicked(
            self.subUpperCard, cfg.sub_comment_time_upperlimit, "子评论上限", 1.0, 5.0, 0.1
            ))

        self.executorCard = OptionsSettingCard(
            cfg.executor,
            FIF.CHAT,
            "执行器线程数",
            "设置并行爬取线程数",
            texts=[str(i) for i in [1, 2, 3, 4, 5, 6]],
            parent=crawlGroup
            )

        crawlGroup.addSettingCard(self.commentFolderCard)
        crawlGroup.addSettingCard(self.mainLowerCard)
        crawlGroup.addSettingCard(self.mainUpperCard)
        crawlGroup.addSettingCard(self.subLowerCard)
        crawlGroup.addSettingCard(self.subUpperCard)
        crawlGroup.addSettingCard(self.executorCard)

        self.vbox.addWidget(crawlGroup)

    def __onFloatValueClicked(self, card, configItem, title, minVal, maxVal, step):
        """
        通用函数，用于点击 PushSettingCard 弹出浮点数输入框
        card: 对应的 PushSettingCard
        configItem: 对应的 ConfigItem
        title: 输入框标题
        minVal, maxVal: 范围
        step: 小数步长
        """
        value, ok = QInputDialog.getDouble(
            self,
            title,
            f"请输入 {title} 值:",
            cfg.get(configItem),
            minVal,
            maxVal,
            decimals=1
            )
        if ok:
            cfg.set(configItem, value)
            card.setContent(str(value))
            self.settings_saved()

    def __onCommentFolderClicked(self):
        folder = QFileDialog.getExistingDirectory(self, "选择保存目录", cfg.get(cfg.save_commentFolder))
        if folder:
            cfg.set(cfg.save_commentFolder, folder)
            self.commentFolderCard.setContent(folder)
            self.settings_saved()

    # -----------------------------
    # 音频播放器设置
    # -----------------------------
    def __initAudioSettings(self):
        audioGroup = SettingCardGroup("音频播放器设置", self.scrollWidget)

        self.successAudioCard = PushSettingCard(
            "成功音效文件",
            FIF.MUSIC,
            "当前文件",
            cfg.get(cfg.success_audio_path),
            parent=audioGroup
            )
        self.successAudioCard.clicked.connect(
            lambda: self.__onAudioFileClicked(cfg.success_audio_path, self.successAudioCard))

        self.failedAudioCard = PushSettingCard(
            "失败音效文件",
            FIF.MUSIC,
            "当前文件",
            cfg.get(cfg.failed_audio_path),
            parent=audioGroup
            )
        self.failedAudioCard.clicked.connect(
            lambda: self.__onAudioFileClicked(cfg.failed_audio_path, self.failedAudioCard))

        self.warningAudioCard = PushSettingCard(
            "警告音效文件",
            FIF.MUSIC,
            "当前文件",
            cfg.get(cfg.warning_audio_path),
            parent=audioGroup
            )
        self.warningAudioCard.clicked.connect(
            lambda: self.__onAudioFileClicked(cfg.warning_audio_path, self.warningAudioCard))

        self.volumeCard = MyRangeSettingCard(
            cfg.volume,
            "音量",
            "设置音量大小",
            parent=audioGroup
            )
        self.volumeCard.releaseChanged.connect(self.settings_saved)

        audioGroup.addSettingCard(self.successAudioCard)
        audioGroup.addSettingCard(self.failedAudioCard)
        audioGroup.addSettingCard(self.warningAudioCard)
        audioGroup.addSettingCard(self.volumeCard)

        self.vbox.addWidget(audioGroup)

    def __onAudioFileClicked(self, configItem, card):
        file, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "./", "音频文件 (*.mp3 *.wav *.flac);;所有文件 (*)"
            )
        if file:
            cfg.set(configItem, file)
            card.setContent(file)
            self.settings_saved()

    # -----------------------------
    # 软件更新设置
    # -----------------------------
    def __initUpdateSettings(self):
        aboutGroup = SettingCardGroup("反馈", self.scrollWidget)
        self.feedbackCard = PrimaryPushSettingCard(
            '提供反馈',
            FIF.FEEDBACK,
            '提供反馈',
            '诉说你遇到的问题，帮助我们改善优化项目',
            aboutGroup
            )
        self.about_card = PrimaryPushSettingCard(
            "关于我们",
            FIF.INFO,
            "点击查看作者信息",
            "关于我们",
            parent=aboutGroup
            )


        aboutGroup.addSettingCard(self.about_card)
        aboutGroup.addSettingCard(self.feedbackCard)
        self.about_card.clicked.connect(self.show_about_us)
        self.feedbackCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl('https://github.com/sxu79r/EchoBi-B-GUI-/issues')))
        self.vbox.addWidget(aboutGroup)

    def show_about_us(self):
        """显示关于我们窗口"""
        self.about_us_signal.emit()

    def settings_saved(self):
        InfoBar.success(
            title='保存成功',
            content='重启后生效',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self
            )
