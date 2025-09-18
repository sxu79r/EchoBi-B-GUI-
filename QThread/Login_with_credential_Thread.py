import json
import os
from bilibili_api import Credential, sync, user
import logging
from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class LoginWithCredentialQThread(QThread):
    """登录凭证管理器"""
    login_with_saved_credential_success = pyqtSignal(object, object)
    login_with_saved_credential_failed = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.config_dir = 'config'
        self.credential_file = os.path.join(self.config_dir, 'credential.env')

    def run(self):
        """加载登录凭证"""
        try:
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
            logger.info("登录凭证加载成功")
            user_info = sync(self.get_user_info(credential))
            self.login_with_saved_credential_success.emit(credential, user_info)
        except Exception as e:
            logger.warning(f"保存的登录凭证已失效，错误：{e}")
            self.login_with_saved_credential_failed.emit(str(e))


    async def get_user_info(self,credential):
        User=user.User(int(credential.dedeuserid), credential=credential)
        user_info = await User.get_user_info()
        return user_info

if __name__ == "__main__":
    thread = LoginWithCredentialQThread()
    thread.start()
