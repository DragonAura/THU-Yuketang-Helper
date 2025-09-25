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
    case_file = os.path.join("output", "fixed_case.json")
    if os.path.exists(case_file):
        try:
            with open(case_file, 'r', encoding='utf-8') as f:
                problems = json.load(f)
                
                # 为每个题目添加图片路径
                for problem in problems:
                    problem['image'] = f"/Users/bytedance/Documents/code/THU-Yuketang-Helper/output/1518018133102002304/{problem['page']}.jpg"
                
                return problems
        except json.JSONDecodeError as e:
            print(f"解析JSON文件出错: {e}")
            # 如果解析出错，返回默认题目
            pass
    else:
        # 如果case.txt不存在，返回默认题目
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
            "image": "/Users/bytedance/Documents/code/THU-Yuketang-Helper/output/1518018133102002304/page.jpg",
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