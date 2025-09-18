<p align="center">
  <img width="256" height="256" alt="256" src="https://github.com/user-attachments/assets/23f056be-a2a3-4e4b-9c04-0f7db257a304" />
</p>

  <h1 align="center">
  EchoBi
</h1>
<p align="center">
  EchoBi,一个用于爬取B站评论的GUI窗口
</p>


## ✨ 功能特性
- [x] 图形化界面，操作简单
- [x] 支持快速登录 / 扫码登录
- [x] 数据爬取、保存与分析
- [x] 结果可视化展示

## 🛠 环境要求
- Windows 10/11
- Python 3.9+
- 依赖库见 `requirements.txt`

## 📖 使用说明

打开软件后，点击头像选择快速登录或扫码登录。

在左侧导航选择功能页：

爬取：输入视频链接，开始获取评论数据。

结果：查看或导出评论结果。

> [!Warning]
> 爬虫时切勿设置太高的请求频率，可能会触发反爬，或有封禁ip的风险

## 📦 安装与运行

### 方式一：源码运行
1. 克隆项目：
 ```bash
   git clone https://github.com/yourname/yourproject.git
   cd yourproject
 ```
2.创建虚拟环境并安装依赖：
```
  python -m venv venv
  venv\Scripts\activate   # Windows
  pip install -r requirements.txt
```
3.运行：
```
  python main.py
```
### 方式二：使用打包好的 exe

下载 [Releases](https://github.com/sxu79r/EchoBi-B-GUI-/releases)
 中的 EchoBi_v1.0_pickedup_.zip。

解压

双击运行EchoBi.exe，无需安装 Python。

## 🤝 贡献
欢迎提交 issue


## 🙏 致谢

感谢[qfluentwidgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
 等优秀开源项目提供支持。

感谢 [Bibili-api站开放的接口](https://github.com/nemo2011/bilibili-api)。

感谢测试和反馈本项目的朋友们。

特别感谢所有为开源生态贡献的人 🙌
