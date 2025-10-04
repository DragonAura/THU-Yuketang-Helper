# 清华大学荷塘雨课堂助手-AI版
基于 *TrickyDeath* 的项目 [RainClassroomAssistant](https://github.com/TrickyDeath/RainClassroomAssitant) 进行修改，以专门适配清华大学的荷塘雨课堂。

基于 [THU-Yuketang-Helper](https://github.com/zhangchi2004/THU-Yuketang-Helper) 进一步适配，适配无法从前端爬取答案后的荷塘雨课堂

## 功能
 - 自动签到
 - AI 答题 / 手动答题，支持在刚上课时答完所有题目，~~然后去愉快摸鱼~~
 - 多线程支持（此脚本支持在有多个正在上课课程的情况下使用）
 - 简洁美观的UI

## 使用程序

首先安装依赖：
```bash
pip install -r requirements.txt
```

然后直接 `python main.py` 即可启动程序。

首先点击设置按钮，按照图形界面进行答题逻辑的设置与 AI api key，具体参考 [阿里官方文档](https://help.aliyun.com/zh/model-studio/get-api-key?spm=a2c4g.11186623.0.0.67c34823GEeyCl)。

然后点击登录，扫描出现的二维码进行登录。

接下来点击启动监听，若有课程即可自动签到。

点击课程名，可显示本课程的所有题目，可以点击“AI 解答所有题目”来自动解答所有题目；还可以点进每道题目，来手动修正答案，或者直接手动作答，或者让AI重新作答。已经作答过且提交到与课堂的题目会被锁住不能修改，同时AI自动解答所有题目时也会自动跳过。