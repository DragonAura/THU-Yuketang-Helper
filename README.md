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

若需要使用 ai 答题功能，需要先获取 api key，具体参考 [阿里官方文档](https://help.aliyun.com/zh/model-studio/get-api-key?spm=a2c4g.11186623.0.0.67c34823GEeyCl)，然后将其输入到 config 里即可。