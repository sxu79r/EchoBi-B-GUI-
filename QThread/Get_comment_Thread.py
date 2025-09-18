from PyQt5.QtCore import QThread, pyqtSignal
from bilibili_api import sync, video, comment
from time import sleep
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from .Load_Settings import cfg


class CommentCrawlerThread(QThread):
    """评论爬取线程"""
    progress_update = pyqtSignal(int, int, str)
    finished = pyqtSignal(list, int, dict, bool)
    error_occurred = pyqtSignal(list, int, dict, str)

    def __init__(self, credential, bv_id):
        super().__init__()
        self.credential = credential
        self.bv_id = bv_id
        self.comments = []
        v = video.Video(bvid=self.bv_id, credential=self.credential)
        self.video_info = sync(v.get_info())
    def run(self):
        try:
            aid = self.video_info['aid']
            total_comments = self.video_info.get('stat', {}).get('reply', 0)

            sub_tasks = []
            page = 1

            self.progress_update.emit(0, total_comments, f"开始爬取视频: {self.video_info['title']}")

            while True:
                c = sync(comment.get_comments(aid, comment.CommentResourceType.VIDEO,
                                              page, credential=self.credential))
                replies = c.get('replies', [])
                if not replies:
                    break

                for cmt in replies:
                    self.comments.append(cmt)
                    if cmt.get("rcount", 0) > 0:
                        sub_tasks.append(cmt['rpid'])

                self.progress_update.emit(len(self.comments), total_comments,
                                          f"已爬取 {len(self.comments)}/{total_comments} 条评论(主评论)")

                page += 1
                sleep(random.uniform(cfg.get(cfg.main_comment_time_lowerlimit),
                                     cfg.get(cfg.main_comment_time_upperlimit)))

            def fetch_sub_comments(rpid):
                sub_cmt = comment.Comment(
                    oid=aid, rpid=rpid,
                    type_=comment.CommentResourceType.VIDEO,
                    credential=self.credential
                    )
                all_subs = []
                sub_index = 1
                while True:
                    sub_c = sync(sub_cmt.get_sub_comments(sub_index, 20))
                    sub_replies = sub_c.get('replies', [])
                    if not sub_replies:
                        break
                    all_subs.extend(sub_replies)
                    sub_index += 1
                    sleep(random.uniform(cfg.get(cfg.sub_comment_time_lowerlimit),
                                         cfg.get(cfg.sub_comment_time_upperlimit)))
                return all_subs

            with ThreadPoolExecutor(max_workers=cfg.get(cfg.executor)) as executor:
                futures = [executor.submit(fetch_sub_comments, rid) for rid in sub_tasks]
                for future in as_completed(futures):
                    sub_replies = future.result()
                    self.comments.extend(sub_replies)
                    self.progress_update.emit(len(self.comments), total_comments,
                                              f"已爬取 {len(self.comments)} 条评论(含子评论)")

            self.finished.emit(self.comments, len(self.comments), self.video_info, True)

        except Exception as e:
            self.error_occurred.emit(self.comments, len(self.comments), self.video_info, str(e))
            return
