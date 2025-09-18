from PyQt5.QtCore import QThread, pyqtSignal
import json, jieba, os
import pandas as pd
from snownlp import SnowNLP
from wordcloud import WordCloud, STOPWORDS
from collections import Counter


class AnalysisThread(QThread):
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)
    progress = pyqtSignal(int, int, str)

    def __init__(self, json_file, stopwords_file="../resource/stopwords.txt"):
        super().__init__()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.json_file = json_file
        self.stopwords_file = os.path.join(script_dir, stopwords_file)

    def run(self):
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                temp_data = json.load(f).get('comments', [])
            new_data_dict = {}
            for key, value in temp_data.items():
                if len(value['replies']) == 0:
                    new_data_dict[key] = value
                    del new_data_dict[key]['replies']
                else:
                    for sub_cmt in value['replies']:
                        temp_key = sub_cmt['rpid']
                        new_data_dict[temp_key] = sub_cmt
            new_data_list = []
            for key, value in new_data_dict.items():
                new_data_list.append(value)
            df = pd.DataFrame(new_data_list)
            df['time'] = pd.to_datetime(df['time'])

            with open(self.stopwords_file, "r", encoding="utf-8") as f:
                stopwords = set([line.strip() for line in f if line.strip()])

            total = len(df)
            clean_messages = []

            for i, msg in enumerate(df['message'], 1):
                words = jieba.lcut(msg.replace("\n", "").strip())
                clean = " ".join([w for w in words if w not in stopwords and len(w) > 1])
                clean_messages.append(clean)
                self.progress.emit(i, total, "分词中")

            df['clean_message'] = clean_messages

            sentiments = []
            for i, msg in enumerate(df['message'], 1):
                sentiments.append(SnowNLP(msg).sentiments)
                self.progress.emit(i, total, "情感分析中")
            df['sentiment'] = sentiments
            df['sentiment_label'] = df['sentiment'].apply(
                lambda s: "正面" if s > 0.6 else ("负面" if s < 0.4 else "中性")
                )

            df['date'] = df['time'].dt.date
            daily_counts = df.groupby('date').size().to_dict()

            all_words = " ".join(df['clean_message'].tolist()).split()
            word_counts = dict(Counter(all_words).most_common(15))

            all_text = " ".join(df['clean_message'].tolist())
            high_text = " ".join(df[df['like'] > 0]['clean_message'].tolist())

            wc_all = WordCloud(font_path='msyh.ttc', width=400, height=300,
                               max_words=15, background_color='white',
                               stopwords=set(STOPWORDS),
                               random_state=42).generate(all_text)
            wc_all.to_file("wordcloud_all.png")
            self.progress.emit(total, total, "生成全部词云完成")

            wc_high = WordCloud(font_path='msyh.ttc', width=400, height=300,
                                max_words=15, background_color='white',
                                stopwords=set(STOPWORDS),
                                random_state=42).generate(high_text)
            wc_high.to_file("wordcloud_high.png")
            self.progress.emit(total, total, "生成高赞词云完成")

            self.finished.emit({
                "df": df,
                "daily_counts": daily_counts,
                "word_counts": word_counts,
                "sentiment": df['sentiment_label'].value_counts().to_dict(),
                "wordcloud_all": "wordcloud_all.png",
                "wordcloud_high": "wordcloud_high.png"
                })

        except Exception as e:
            self.failed.emit(str(e))
