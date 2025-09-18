import json
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class SaveCommentThread(QThread):
    """保存评论数据的线程类"""

    save_progress = pyqtSignal(int, int, str)
    save_finished = pyqtSignal(str, bool)
    save_error = pyqtSignal(str)

    def __init__(self, comments, video_info, filename):
        super().__init__()
        self.comments = comments
        self.video_info = video_info
        self.filename = filename
        self.is_running = True

    def run(self):
        """线程运行函数"""
        try:
            if not self.comments:
                self.save_error.emit("没有评论数据可保存")
                return

            total_steps = 3
            current_step = 0

            current_step += 1
            self.save_progress.emit(current_step, total_steps, "正在处理评论数据...")
            processed_comments = self.process_comments()

            if not self.is_running:
                return

            current_step += 1
            self.save_progress.emit(current_step, total_steps, "正在构建数据结构...")
            data_to_save = self.build_data_structure(processed_comments)

            if not self.is_running:
                return

            current_step += 1
            self.save_progress.emit(current_step, total_steps, "正在保存文件...")
            success = self.save_to_file(data_to_save)

            if success:
                self.save_finished.emit(self.filename, True)
            else:
                self.save_finished.emit("", False)

        except Exception as e:
            error_msg = f"保存过程中出现错误: {str(e)}"
            logger.error(error_msg)
            self.save_error.emit(error_msg)
            self.save_finished.emit("", False)

    def process_comments(self):
        """处理评论数据"""
        processed_comments = {}
        children_map = {}
        total_comments=len(self.comments)
        i = 1
        for cmt in self.comments:
            is_sub_reply = (cmt['parent'] != 0)
            if not is_sub_reply:
                processed_cmt = extract_comment_info(cmt, is_sub_reply=False)
                processed_cmt['replies'] = []
                processed_comments[cmt['rpid']] = processed_cmt
            else:
                processed_reply = extract_comment_info(cmt, is_sub_reply=True)
                children_map.setdefault(cmt['parent'], []).append(processed_reply)
            i+=1
            if i % 100 == 0:
                progress_msg = f"已分流{i}/{total_comments} 条评论"
                self.save_progress.emit(1, 3, progress_msg)
        i=0
        for parent_id, replies in children_map.items():
            if parent_id in processed_comments:
                processed_comments[parent_id]['replies'].extend(replies)
            if i % 100 == 0:
                progress_msg = f"已处理{i}/{total_comments} 条子评论"
                self.save_progress.emit(1, 3, progress_msg)

        return processed_comments

    def build_data_structure(self, processed_comments):
        """构建完整的数据结构"""
        return {
            "metadata": {
                "video_info": {
                    "aid": self.video_info.get('aid'),
                    "bvid": self.video_info.get('bvid'),
                    "title": self.video_info.get('title'),
                    "author": self.video_info.get('owner', {}).get('name'),
                    "crawl_time": datetime.now().isoformat()
                    },
                "main_comment_count": len(processed_comments),
                "total_comments": self.video_info.get('stat', {}).get('reply', 0),
                "save_time": datetime.now().isoformat()
                },
            "comments": processed_comments
            }

    def save_to_file(self, data):
        """保存数据到文件"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            error_msg = f"文件保存失败: {str(e)}"
            self.save_error.emit(error_msg)
            return False

    def stop(self):
        """停止线程"""
        self.is_running = False


def extract_comment_info(comment_data: Dict, is_sub_reply) -> Dict:
    """

    从评论数据中提取所需信息

    Args:
        comment_data: 原始评论数据

    Returns:
        提取后的评论信息
    """
    return {
        "rpid": comment_data.get('rpid', 0),
        "user_id": comment_data.get('member', {}).get('mid', 0),
        "uname": comment_data.get('member', {}).get('uname', '未知用户'),
        "message": comment_data.get('content', {}).get('message', ''),
        "time": datetime.fromtimestamp(comment_data.get('ctime', 0)).isoformat(),
        "sex": comment_data.get('member', {}).get('sex', ''),
        "Ip": comment_data.get('reply_control', {}).get('location', ''),
        "like": comment_data.get('like', 0),
        "is_sub_reply": is_sub_reply
        }