import requests
import threading
import random
import time
from urllib3.util import retry
import websocket
import json
from Scripts.Utils import get_user_info, dict_result, calculate_waittime
import os
from dashscope import MultiModalConversation
import tkinter as tk
from tkinter import ttk
from typing import List, Union, Optional

import sys
from typing import List, Union, Optional

def popup_input(
    title: str = "Input",
    prompt: str = "",
    input_type: str = "entry",  # 'entry', 'entries', 'radio', 'check'
    options: Optional[List[str]] = None,
    fields: Optional[List[str]] = None,
    default: Union[str, List[str], None] = None
) -> Union[str, List[str], None]:
    """
    纯命令行交互式输入函数（无 GUI，仅终端）。
    
    支持：
      - entry: 单行文本（可带默认值）
      - entries: 多字段填空（返回列表）
      - radio: 单选（输入序号或内容）
      - check: 多选（输入逗号分隔的序号，如 1,3,5）
    
    默认值规则：
      - entry: str
      - entries: List[str]
      - radio: str（必须在 options 中）
      - check: List[str]（子集 of options）
    """
    print(f"\n=== {title} ===")
    if prompt:
        print(prompt)

    if input_type == "entry":
        dft_str = f" [{default}]" if default is not None else ""
        while True:
            try:
                user_input = input(f"请输入{dft_str}：").strip()
                if user_input == "" and default is not None:
                    return str(default)
                return [user_input]
            except (KeyboardInterrupt, EOFError):
                print("\n取消输入。")
                return None

    elif input_type == "entries":
        if not fields:
            raise ValueError("fields must be provided for 'entries'")
        n = len(fields)
        if default is None:
            defaults = [""] * n
        elif isinstance(default, list):
            if len(default) != n:
                raise ValueError("Length of 'default' must match 'fields'")
            defaults = [str(d) if d is not None else "" for d in default]
        else:
            raise ValueError("'default' for 'entries' must be a list or None")

        results = []
        for i, field in enumerate(fields):
            dft = defaults[i]
            dft_str = f" [{dft}]" if dft != "" else ""
            try:
                val = input(f"{field}{dft_str}：").strip()
                if val == "" and dft != "":
                    val = dft
                results.append(val)
            except (KeyboardInterrupt, EOFError):
                print("\n取消输入。")
                return None
        return results

    elif input_type in ("radio", "check"):
        if not options:
            raise ValueError("options must be provided for radio/check")
        print("\n选项：")
        for i, opt in enumerate(options, 1):
            print(f"  {i}. {opt}")

        # 处理默认值提示
        if input_type == "radio":
            dft_opt = default if default in options else None
            dft_idx = options.index(dft_opt) + 1 if dft_opt else None
            dft_hint = f" [{dft_idx}]" if dft_idx else ""
            prompt_str = f"请选择一项{dft_hint}（输入序号）："
        else:  # check
            if isinstance(default, (list, tuple)):
                valid_defaults = [opt for opt in default if opt in options]
                dft_indices = [str(options.index(opt) + 1) for opt in valid_defaults]
                dft_hint = f" [{','.join(dft_indices)}]" if dft_indices else ""
            else:
                dft_hint = ""
            prompt_str = f"请选择多项{dft_hint}（输入序号，逗号分隔，如 1,3）："

        while True:
            try:
                user_input = input(prompt_str).strip()
                if not user_input:
                    if input_type == "radio" and dft_idx:
                        chosen_indices = [dft_idx]
                        break
                    elif input_type == "check" and 'dft_indices' in locals() and dft_indices:
                        chosen_indices = [int(x) for x in dft_indices]
                        break
                    else:
                        print("未输入有效选项，请重试。")
                        continue

                # 解析输入
                if input_type == "radio":
                    if user_input.isdigit():
                        idx = int(user_input)
                        if 1 <= idx <= len(options):
                            chosen_indices = [idx]
                            break
                    print("请输入有效序号（如 1, 2, 3）")
                else:  # check
                    parts = [p.strip() for p in user_input.split(",") if p.strip()]
                    indices = []
                    valid = True
                    for p in parts:
                        if p.isdigit():
                            idx = int(p)
                            if 1 <= idx <= len(options):
                                indices.append(idx)
                            else:
                                valid = False
                        else:
                            valid = False
                    if valid and indices:
                        chosen_indices = sorted(set(indices))  # 去重+排序
                        break
                    else:
                        print("请输入有效序号，逗号分隔（如 1,3,5）")
            except (KeyboardInterrupt, EOFError):
                print("\n取消输入。")
                return None

        if input_type == "radio":
            return [options[chosen_indices[0] - 1]]
        else:
            return [options[i - 1] for i in chosen_indices]

    else:
        raise ValueError("input_type must be 'entry', 'entries', 'radio', or 'check'")

wss_url = "wss://pro.yuketang.cn/wsapp/"
class Lesson:
    def __init__(self,lessonid,lessonname,classroomid,main_ui):
        self.classroomid = classroomid
        self.lessonid = lessonid
        self.lessonname = lessonname
        self.sessionid = main_ui.config["sessionid"]
        self.headers = {
            "Cookie":"sessionid=%s" % self.sessionid,
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0",
        }
        self.receive_danmu = {}
        self.sent_danmu_dict = {}
        self.danmu_dict = {}
        self.problems_ls = []
        self.unlocked_problem = []
        self.classmates_ls = []
        self.add_message = main_ui.add_message_signal.emit
        self.add_course = main_ui.add_course_signal.emit
        self.del_course = main_ui.del_course_signal.emit
        self.config = main_ui.config
        code, rtn = get_user_info(self.sessionid)
        self.user_uid = rtn["id"]
        self.user_uname = rtn["name"]
        self.main_ui = main_ui

    def _get_ppt(self,presentationid):
        # 获取课程各页ppt
        r = requests.get(url="https://pro.yuketang.cn/api/v3/lesson/presentation/fetch?presentation_id=%s" % (presentationid),headers=self.headers,proxies={"http": None,"https":None})
        return dict_result(r.text)["data"]

    def get_problems(self,presentationid):
        # 获取课程ppt中的题目
        data = self._get_ppt(presentationid)
        # print(data["slides"][0])
        return_problem = []
        os.makedirs(os.path.join("output", presentationid),exist_ok=True)
        for idx, slide in enumerate(data["slides"]):
            if "cover" in slide.keys() and not os.path.exists(os.path.join("output", presentationid,"%s.jpg" % idx)):
                r = requests.get(slide["cover"],headers=self.headers,proxies={"http": None,"https":None})
                if r.status_code == 200:
                    with open(os.path.join("output", presentationid,"%s.jpg" % idx),"wb") as f:
                        f.write(r.content)
                        self.add_message("下载图片成功，路径为：%s" % os.path.join("output", presentationid,"%s.jpg" % idx),3)
                else:
                    self.add_message("下载图片失败，状态码：%s，路径为：%s" % (r.status_code,os.path.join("output", presentationid,"%s.jpg" % idx)),4)

            if "problem" in slide.keys():
                # replace with abs path
                print(slide["problem"])
                local_path = os.path.join(os.path.abspath("output"), presentationid,"%s.jpg" % idx)
                image_path = f"file://{local_path}"
                messages = [{"role": "system",
                            "content": [{"text": "You are a helpful assistant."}]},
                            {'role':'user',
                            'content': [{'image': image_path},
                                        {'text': '请以JSON格式回答图片中的问题。如果是选择题，则返回{{"question": "问题", "answer": ["选项（A/B/C/...）"]}}，选项为圆形则为单选，选项为矩形则为多选；如果是填空题，则返回{{"question": "问题", "answer": ["填空1答案", "填空2答案", ...]}}'}]}]

                have_answer = False
                retry_count = 0
                slide["problem"]["page"] = idx
                while not have_answer and retry_count < 5:
                    try:
                        response = MultiModalConversation.call(
                            api_key="sk-b6f093b32dd5401eb2988d963c85df18",
                            model='qwen-vl-max-latest',
                            messages=messages,
                            response_format={"type": "json_object"},
                            vl_high_resolution_images=True)
                        json_output = response["output"]["choices"][0]["message"].content[0]["text"]
                        res = json.loads(json_output)
                        self.add_message("解析JSON成功，页数：%s, 原始输出：%s，重试第%s次" % (idx, json_output,retry_count),3)
                        if slide["problem"]["blanks"]:
                            assert len(slide["problem"]["blanks"]) == len(res["answer"]), "空数与答案数不相等，请重新检查！"
                        slide["problem"]["answers"] = res["answer"]
                        have_answer = True
                    except json.JSONDecodeError:
                        self.add_message("解析JSON失败，原始输出：%s，重试第%s次" % (json_output,retry_count),4)
                        retry_count += 1
                        if retry_count >= 5:
                            self.add_message("解析JSON失败，原始输出：%s，重试第%s次，已放弃" % (json_output,retry_count),4)
                            slide["problem"]["answers"] = ["A"]

                problem = slide["problem"]
                print(problem)
                title = "是否需要修正答案"
                if problem["problemType"] == 1:
                    prompt = problem["body"] + f"问题的页码为 {problem['page']}"
                    input_type = "radio"
                    options = [d["key"]for d in problem["options"]]
                    fields = None
                    default = problem["answers"][0]
                    answers = popup_input(title,prompt,input_type,options,default=default)
                    problem["answers"] = answers
                elif problem["problemType"] == 2 or problem["problemType"] == 3:
                    prompt = problem["body"] + f"问题的页码为 {problem['page']}"
                    input_type = "check"
                    options = [d["key"] for d in problem["options"]]
                    fields = None
                    default = problem["answers"]
                    answers = popup_input(title,prompt,input_type,options,default=default)  
                    problem["answers"] = answers
                elif problem["blanks"]: # 暂时不确定填空是什么
                    prompt = problem["body"] + f"问题的页码为 {problem['page']}"
                    input_type = "entries"
                    fields = [f"填空{i}" for i in range(len(problem["blanks"]))]
                    if len(fields) != len(problem["answers"]):
                        problem["answers"] = [""] * len(fields)
                    default = problem["answers"]
                    answers = popup_input(title,prompt,input_type,fields,default=default)  
                    problem["answers"] = answers
                return_problem.append(problem)
        print(return_problem)
        return return_problem

    def answer_questions(self,problemid,problemtype,answer,limit):
        # 回答问题
        if answer:
            wait_time = calculate_waittime(limit, self.config["answer_config"]["answer_delay"]["type"], self.config["answer_config"]["answer_delay"]["custom"]["time"])
            if wait_time != 0:
                meg = "%s检测到问题，将在%s秒后自动回答，答案为%s" % (self.lessonname,wait_time,answer)
                # threading.Thread(target=say_something,args=(meg,)).start()
                self.add_message(meg,3)
                time.sleep(wait_time)
            else:
                meg = "%s检测到问题，剩余时间小于15秒，将立即自动回答，答案为%s" % (self.lessonname,answer)
                self.add_message(meg,3)
                # threading.Thread(target=say_something,args=(meg,)).start()
            data = {"problemId":problemid,"problemType":problemtype,"dt":int(time.time()),"result":answer}
            r = requests.post(url="https://pro.yuketang.cn/api/v3/lesson/problem/answer",headers=self.headers,data=json.dumps(data),proxies={"http": None,"https":None})
            return_dict = dict_result(r.text)
            if return_dict["code"] == 0:
                meg = "%s自动回答成功" % self.lessonname
                self.add_message(meg,4)
                # threading.Thread(target=say_something,args=(meg,)).start()
                return True
            else:
                meg = "%s自动回答失败，原因：%s" % (self.lessonname,return_dict["msg"].replace("_"," "))
                self.add_message(meg,4)
                # threading.Thread(target=say_something,args=(meg,)).start()
                return False
        else:
            if limit == -1:
                meg = "%s的问题没有找到答案，该题不限时，请尽快前往荷塘雨课堂回答" % (self.lessonname)
            else:
                meg = "%s的问题没有找到答案，请在%s秒内前往荷塘雨课堂回答" % (self.lessonname,limit)
            # threading.Thread(target=say_something,args=(meg,)).start()
            self.add_message(meg,4)
            return False
    
    def on_open(self, wsapp):
        self.handshake = {"op":"hello","userid":self.user_uid,"role":"student","auth":self.auth,"lessonid":self.lessonid}
        wsapp.send(json.dumps(self.handshake))

    def checkin_class(self):
        r = requests.post(url="https://pro.yuketang.cn/api/v3/lesson/checkin",headers=self.headers,data=json.dumps({"source":5,"lessonId":self.lessonid}),proxies={"http": None,"https":None})
        set_auth = r.headers.get("Set-Auth",None)
        times = 1
        while not set_auth and times <= 3:
            set_auth = r.headers.get("Set-Auth",None)
            times += 1
            time.sleep(1)
        self.headers["Authorization"] = "Bearer %s" % set_auth
        return dict_result(r.text)["data"]["lessonToken"]

    def on_message(self, wsapp, message):
        data = dict_result(message)
        op = data["op"]
        if op == "hello":
            presentations = list(set([slide["pres"] for slide in data["timeline"] if slide["type"]=="slide"]))
            current_presentation = data["presentation"]
            if current_presentation not in presentations:
                presentations.append(current_presentation)
            for presentationid in presentations:
                self.problems_ls.extend(self.get_problems(presentationid))
            self.unlocked_problem = data["unlockedproblem"]
            for problemid in self.unlocked_problem:
                self._current_problem(wsapp, problemid)
        elif op == "unlockproblem":
            self.start_answer(data["problem"]["sid"],data["problem"]["limit"])
        elif op == "lessonfinished":
            meg = "%s下课了" % self.lessonname
            # threading.Thread(target=say_something,args=(meg,)).start()
            self.add_message(meg,7)
            wsapp.close()
        elif op == "presentationupdated":
            self.problems_ls.extend(self.get_problems(data["presentation"]))
        elif op == "presentationcreated":
            self.problems_ls.extend(self.get_problems(data["presentation"]))
        elif op == "newdanmu" and self.config["auto_danmu"]:
            current_content = data["danmu"].lower()
            uid = data["userid"]
            sent_danmu_user = User(uid)
            if sent_danmu_user in self.classmates_ls:
                for i in self.classmates_ls:
                    if i == sent_danmu_user:
                        meg = "%s课程的%s%s发送了弹幕：%s" %(self.lessonname,i.sno,i.name,data["danmu"])
                        self.add_message(meg,2)
                        break
            else:
                self.classmates_ls.append(sent_danmu_user)
                sent_danmu_user.get_userinfo(self.classroomid,self.headers)
                meg = "%s课程的%s%s发送了弹幕：%s" %(self.lessonname,sent_danmu_user.sno,sent_danmu_user.name,data["danmu"])
                self.add_message(meg,2)
            now = time.time()
            # 收到一条弹幕，尝试取出其之前的所有记录的列表，取不到则初始化该内容列表
            try:
                same_content_ls = self.danmu_dict[current_content]
            except KeyError:
                self.danmu_dict[current_content] = []
                same_content_ls = self.danmu_dict[current_content]
            # 清除超过60秒的弹幕记录
            for i in same_content_ls:
                if now - i > 60:
                    same_content_ls.remove(i)
            # 如果当前的弹幕没被发过，或者已发送时间超过60秒
            if current_content not in self.sent_danmu_dict.keys() or now - self.sent_danmu_dict[current_content] > 60:
                if len(same_content_ls) + 1 >= self.config["danmu_config"]["danmu_limit"]:
                    self.send_danmu(current_content)
                    same_content_ls = []
                    self.sent_danmu_dict[current_content] = now
                else:
                    same_content_ls.append(now)
        elif op == "callpaused":
            meg = "%s点名了，点到了：%s" % (self.lessonname, data["name"])
            if self.user_uname == data["name"]:
                self.add_message(meg,5)
            else:
                self.add_message(meg,6)
        # 程序在上课中途运行，由_current_problem发送的已解锁题目数据，得到的返回值。
        # 此处需要筛选未到期的题目进行回答。
        elif op == "probleminfo":
            if data["limit"] != -1:
                time_left = int(data["limit"]-(int(data["now"]) - int(data["dt"]))/1000)
            else:
                time_left = data["limit"]
            # 筛选未到期题目
            if time_left > 0 or time_left == -1:
                if self.config["auto_answer"]:
                    self.start_answer(data["problemid"],time_left)
                else:
                    if time_left == -1:
                        meg = "%s检测到问题，该题不限时，请尽快前往荷塘雨课堂回答" % (self.lessonname)
                        self.add_message(meg,3)
                    else:
                        meg = "%s检测到问题，请在%s秒内前往荷塘雨课堂回答" % (self.lessonname,time_left)

    def start_answer(self, problemid, limit):
        for promblem in self.problems_ls:
            if promblem["problemId"] == problemid:
                if promblem["result"] is not None:
                    # 如果该题已经作答过，直接跳出函数以忽略该题
                    # 该情况理论上只会出现在启动监听时
                    return
                # blanks = promblem.get("blanks",[])
                # answers = []
                answers = promblem.get("answers",[])
                threading.Thread(target=self.answer_questions,args=(promblem["problemId"],promblem["problemType"],answers,limit)).start()
                print("Try answer")
                break
        else:
            if limit == -1:
                meg = "%s的问题没有找到答案，该题不限时，请尽快前往荷塘雨课堂回答" % (self.lessonname)
            else:
                meg = "%s的问题没有找到答案，请在%s秒内前往荷塘雨课堂回答" % (self.lessonname,limit)
            self.add_message(meg,4)
            # threading.Thread(target=say_something,args=(meg,)).start()

    
    def _current_problem(self, wsapp, promblemid):
        # 为获取已解锁的问题详情信息，向wsapp发送probleminfo
        query_problem = {"op":"probleminfo","lessonid":self.lessonid,"problemid":promblemid,"msgid":1}
        wsapp.send(json.dumps(query_problem))
    
    def start_lesson(self, callback):
        self.auth = self.checkin_class()
        rtn = self.get_lesson_info()
        teacher = rtn["teacher"]["name"]
        title = rtn["title"]
        timestamp = rtn["startTime"] // 1000
        time_str = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(timestamp))
        index = self.main_ui.tableWidget.rowCount()
        self.add_course([self.lessonname,title,teacher,time_str],index)
        self.wsapp = websocket.WebSocketApp(url=wss_url,header=self.headers,on_open=self.on_open,on_message=self.on_message)
        self.wsapp.run_forever()
        meg = "%s监听结束" % self.lessonname
        self.add_message(meg,7)
        self.del_course(index)
        # threading.Thread(target=say_something,args=(meg,)).start()
        return callback(self)
    
    def send_danmu(self,content):
        url = "https://pro.yuketang.cn/api/v3/lesson/danmu/send"
        data = {
            "extra": "",
            "fromStart": "50",
            "lessonId": self.lessonid,
            "message": content,
            "requiredCensor": False,
            "showStatus": True,
            "target": "",
            "userName": "",
            "wordCloud": True
        }
        r = requests.post(url=url,headers=self.headers,data=json.dumps(data),proxies={"http": None,"https":None})
        if dict_result(r.text)["code"] == 0:
            meg = "%s弹幕发送成功！内容：%s" % (self.lessonname,content)
        else:
            meg = "%s弹幕发送失败！内容：%s" % (self.lessonname,content)
        self.add_message(meg,1)
    
    def get_lesson_info(self):
        url = "https://pro.yuketang.cn/api/v3/lesson/basic-info"
        r = requests.get(url=url,headers=self.headers,proxies={"http": None,"https":None})
        return dict_result(r.text)["data"]
        

    def __eq__(self, other):
        return self.lessonid == other.lessonid

class User:
    def __init__(self, uid):
        self.uid = uid
    
    def get_userinfo(self, classroomid, headers):
        r = requests.get("https://pro.yuketang.cn/v/course_meta/fetch_user_info_new?query_user_id=%s&classroom_id=%s" % (self.uid,classroomid),headers=headers,proxies={"http": None,"https":None})
        data = dict_result(r.text)["data"]
        self.sno = data["school_number"]
        self.name = data["name"]