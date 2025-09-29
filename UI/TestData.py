import json
import os

# 测试课程数据
test_course = {
    "lessonId": "test_lesson_1",
    "courseName": "test",
    "classroomId": "test_classroom_1",
    "status": 1,  # 进行中
    "progress": "50%"
}

# 从fixed_case.json加载题目数据
def load_test_problems():
    return [{
        "problemId": "default_1",
        "problemType": 1,
        "body": "测试题目1",
        "options": [
            {"key": "A", "value": "选项A"},
            {"key": "B", "value": "选项B"},
            {"key": "C", "value": "选项C"},
            {"key": "D", "value": "选项D"}
        ],
        "answers": [],
        "image": "None",
        "page": 1
    }]

# 获取测试课程列表
def get_test_lessons():
    return [test_course]

# 创建测试课程对象
def create_test_lesson(main_ui):
    from Scripts.Classes import Lesson
    lesson = Lesson(
        lessonid=test_course["lessonId"],
        lessonname=test_course["courseName"],
        classroomid=test_course["classroomId"],
        main_ui=main_ui
    )
    # 加载测试题目
    lesson.problems_ls = load_test_problems()
    return lesson
