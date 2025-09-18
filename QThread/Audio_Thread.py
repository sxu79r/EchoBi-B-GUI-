import os
import threading
import time
from PyQt5.QtCore import QObject, pyqtSignal
from .Load_Settings import cfg

try:
    import pygame

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    from playsound import playsound

    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False


class AudioThread(QObject):
    """纯Python音频播放器 - 后台播放，无需第三方播放器"""


    def __init__(self):
        super().__init__()
        self.audio_files = {}
        self.volume = cfg.get(cfg.volume)
        self.enabled = True
        self.is_playing = False
        self.current_thread = None
        self._stop_requested = False

        self.init_audio_system()
        self.load_audio_files()

    def init_audio_system(self):
        """初始化音频系统"""
        self.audio_available = False

        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                self.audio_available = True
                return
            except Exception as e:
                print(f"❌ Pygame初始化失败: {e}")

        if PLAYSOUND_AVAILABLE:
            self.audio_available = True
            return

        print("❌ 没有可用的音频库，音效功能将禁用")

    def load_audio_files(self):
        """加载音频文件"""
        sound_mapping = {
            'success': cfg.get(cfg.success_audio_path),
            'error': cfg.get(cfg.failed_audio_path),
            'warning': cfg.get(cfg.warning_audio_path),
            'notification': ''
            }

        for sound_type, file_list in sound_mapping.items():
            abs_path = self.get_absolute_path(file_list)
            if abs_path and os.path.exists(abs_path):
                self.audio_files[sound_type] = abs_path

    def get_absolute_path(self, relative_path):
        """获取绝对路径"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            search_paths = [
                os.path.join(base_dir, relative_path),
                os.path.join(base_dir, '..', relative_path),
                os.path.join(base_dir, '../assets', relative_path),
                os.path.abspath(relative_path)
                ]

            for path in search_paths:
                if os.path.exists(path):
                    return os.path.normpath(path)
            return None
        except:
            return None

    def play_success(self):
        """播放成功音效"""
        return self._play('success')

    def play_error(self):
        """播放错误音效"""
        return self._play('error')

    def play_warning(self):
        """播放完成音效"""
        return self._play('warning')

    def play_notification(self):
        """播放通知音效"""
        return self._play('notification')

    def _play(self, sound_type):
        """播放指定类型的音效"""
        if not self.enabled or not self.audio_available:
            return False

        file_path = self.audio_files.get(sound_type)
        if not file_path:
            return False

        self.stop()

        self._stop_requested = False
        self.current_thread = threading.Thread(
            target=self._play_in_thread,
            args=(sound_type, file_path),
            daemon=True
            )
        self.current_thread.start()
        return True

    def _play_in_thread(self, sound_type, file_path):
        """在线程中播放音频"""
        self.is_playing = True

        if PYGAME_AVAILABLE:
            self._play_with_pygame(file_path)
        elif PLAYSOUND_AVAILABLE:
            self._play_with_playsound(file_path)
    def _play_with_pygame(self, file_path):
        """使用Pygame播放音频"""
        try:
            pygame_volume = max(0.0, min(1.0, self.volume / 100.0))

            sound = pygame.mixer.Sound(file_path)
            sound.set_volume(pygame_volume)
            channel = sound.play()

            while channel and channel.get_busy() and not self._stop_requested:
                time.sleep(0.1)

            if self._stop_requested and channel:
                channel.stop()

        except Exception as e:
            raise Exception(f"Pygame播放失败: {e}")

    def _play_with_playsound(self, file_path):
        """使用playsound播放音频"""
        try:
            playsound(file_path, block=True)
        except Exception as e:
            raise Exception(f"playsound播放失败: {e}")

    def stop(self):
        """停止当前播放"""
        self._stop_requested = True
        if self.is_playing and self.current_thread:
            self.current_thread.join(timeout=0.5)
        self._stop_requested = False

    def set_volume(self, volume):
        """设置音量 (0-100)"""
        if 0 <= volume <= 100:
            self.volume = volume
            return True
        return False

    def get_volume(self):
        """获取当前音量"""
        return self.volume

    def enable(self):
        """启用音频"""
        self.enabled = True

    def disable(self):
        """禁用音频"""
        self.enabled = False
        self.stop()

    def is_audio_available(self):
        """检查音频系统是否可用"""
        return self.audio_available

    def get_audio_status(self):
        """获取音频状态信息"""
        status = {
            'enabled': self.enabled,
            'volume': self.volume,
            'playing': self.is_playing,
            'system_available': self.audio_available,
            'pygame_available': PYGAME_AVAILABLE,
            'playsound_available': PLAYSOUND_AVAILABLE,
            'audio_files': {}
            }

        for sound_type, file_path in self.audio_files.items():
            status['audio_files'][sound_type] = {
                'path': file_path,
                'exists': os.path.exists(file_path) if file_path else False
                }

        return status