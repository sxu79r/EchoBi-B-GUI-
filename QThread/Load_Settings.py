import os
from qfluentwidgets import (
    qconfig, QConfig, ConfigItem, OptionsConfigItem, OptionsValidator, RangeConfigItem, RangeValidator, FolderValidator
    )


class Config(QConfig):
    """ 应用配置类，保存所有设置项 """

    # ------------------------------
    # 爬虫相关配置
    # ------------------------------
    save_commentFolder = ConfigItem(
        "Crawl", "Save_path", "", FolderValidator())
    main_comment_time_upperlimit = RangeConfigItem("Crawl", "Main_Time_UpperLimit", 1.5, RangeValidator(1, 5))
    main_comment_time_lowerlimit = RangeConfigItem("Crawl", "Main_Time_LowerLimit", 0.8, RangeValidator(0.5, 3))
    sub_comment_time_upperlimit = RangeConfigItem("Crawl", "Sub_Time_UpperLimit", 1.5, RangeValidator(1, 5))
    sub_comment_time_lowerlimit = RangeConfigItem("Crawl", "Sub_Time_LowerLimit", 0.8, RangeValidator(0.5, 3))
    executor = OptionsConfigItem("Crawl", "Executor", 4, OptionsValidator([1, 2, 3, 4, 5, 6]))
    # ------------------------------
    # 音频播放器相关配置
    # ------------------------------
    success_audio_path = ConfigItem("Audio", "Success_Audio_path", "../sound/邦邦咔邦.mp3")
    failed_audio_path = ConfigItem("Audio", "Failed_Audio_path", "../sound/牡蛎牡蛎.mp3")
    warning_audio_path = ConfigItem("Audio", "Warning_Audio_path", "")
    volume = RangeConfigItem("Audio", "Volume", 60, RangeValidator(0, 100))



# ================================
# 加载配置
# ================================

script_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(script_dir, '../config/config.json')
cfg = Config()
qconfig.load(path, cfg)

if __name__ == '__main__':
    simple_cfg = Config()
    simple_cfg.save()
    print(1)
