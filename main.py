from GUI.MainWindows import BilibiliCommentGUI
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QRect, QUrl
from QThread.Load_Settings import cfg
import sys
import os
from PyQt5.QtGui import QIcon
from qfluentwidgets import setTheme, Theme
import traceback


def save_config_on_exit():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, 'config/config.json')
    cfg.save(path)
    print(1)


def main():
    """主函数"""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)

    window = BilibiliCommentGUI()
    window.show()

    app.aboutToQuit.connect(save_config_on_exit)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
