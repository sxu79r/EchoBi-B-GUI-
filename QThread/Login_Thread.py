import asyncio
from PyQt5.QtCore import pyqtSignal, QThread
from bilibili_api import login_v2, user



class QrLoginThread(QThread):
    """子线程执行二维码登录逻辑"""
    login_success = pyqtSignal(object, object)
    login_failed = pyqtSignal(str)
    qr_ready = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            credential, user_info = loop.run_until_complete(self.qr_login())
            self.login_success.emit(credential, user_info)
        except Exception as e:
            self.login_failed.emit(str(e))

    async def qr_login(self):
        qr_code = login_v2.QrCodeLogin(platform=login_v2.QrCodeLoginChannel.WEB)
        await qr_code.generate_qrcode()

        qr_code_url = qr_code.get_qrcode_picture().url[7:]
        qr_code_url = qr_code_url.replace("\\", "/")

        self.qr_ready.emit(qr_code_url)


        while not qr_code.has_done():
            print(await qr_code.check_state())
            await asyncio.sleep(1)

        credential = qr_code.get_credential()
        User = user.User(int(credential.dedeuserid), credential=credential)
        user_info = await User.get_user_info()
        return credential, user_info
