import cv2
import time
from image_processing import *
from plate_recognition import plate_detect_rec
from text_to_speech import TTSManager
from overstaying_capture import capture_overstaying_vehicle
from notification_system import send_email, send_sms_smsbao

class PlateRecognitionSystem:
    def __init__(self, udp_url):
        # 创建文本到语音（TTS）管理器实例
        self.tts_manager = TTSManager()

        # 定义特定的车牌列表
        self.special_plates = ["苏FS8888", "车牌B", "车牌C"]

        # 初始化车牌识别对象
        self.plateRec = plate_detect_rec()
        self.img_size = (320, 320)

        # 初始化状态变量
        self.state_vars = {
            "last_seen_plate": None,
            "photo_taken": False,
            "welcome_message_played": False,
            "plate_seen_count": 0,
            "warning_repeat_count": 0,
            "overstay_detected": False,
            "valid_plate_detected": False,
            "message_played": False,
            "last_spoken_plate_time": {},  # 仅记录触发语音播报的车牌最后一次被识别的时间
            "last_seen_times": {},  # 记录每个车牌最后一次被识别的时间和出现次数
            "first_seen_times": {},  # 记录每个车牌首次被识别的时间
        }

        # 设置时间窗口和出现次数阈值
        self.TIME_WINDOW = 5  # 时间窗口，单位为秒
        self.COUNT_THRESHOLD = 3  # 连续出现次数阈值
        self.DEPARTURE_DELAY = 3 # 设置离开判断的延迟时间为3秒

        # 初始化RTSP URL
        self.udp_url = udp_url

    def process_plate_recognition(self, img):
        result, img0 = self.plateRec(img, self.img_size)

        # 检查车牌识别结果
        if result and len(result[0]['plate_no']) >= 5:
            plate_no = result[0]['plate_no']
            self.state_vars["valid_plate_detected"] = True
            current_time = time.time()  # 获取当前时间
            self.update_plate_info(plate_no, current_time, img0)  # 现在传递img0

        else:
            # 当不再识别到车牌时的处理
            self.process_departure(time.time())

        return result, img0

    def update_plate_info(self, plate_no, current_time, img0):
        # 更新车牌最后一次被识别的时间和出现次数
        if plate_no in self.state_vars["last_seen_times"]:
            last_time, count = self.state_vars["last_seen_times"][plate_no]
            if current_time - last_time <= self.TIME_WINDOW:
                count += 1
            else:
                count = 1
        else:
            count = 1
        self.state_vars["last_seen_times"][plate_no] = (current_time, count)

        # 检查是否是新的车牌
        if plate_no != self.state_vars["last_seen_plate"]:
            self.state_vars["last_seen_plate"] = plate_no
            self.state_vars["plate_seen_count"] = 1
            self.state_vars["warning_repeat_count"] = 0
            self.state_vars["overstay_detected"] = False
            self.state_vars["photo_taken"] = False
            self.state_vars["welcome_message_played"] = False
            self.state_vars["message_played"] = False

            # 重置其他车牌的出现次数
            for key in self.state_vars["last_seen_times"]:
                if key != plate_no:
                    self.state_vars["last_seen_times"][key] = (self.state_vars["last_seen_times"][key][0], 0)

            self.state_vars["first_seen_times"][plate_no] = current_time  # 记录首次识别时间
        else:
            self.state_vars["plate_seen_count"] += 1
            stay_duration = current_time - self.state_vars["first_seen_times"][self.state_vars["last_seen_plate"]]
            self.handle_warnings(plate_no, stay_duration, current_time, img0)  # 传递img0

    def handle_warnings(self, plate_no, stay_duration, current_time, img0):
        # 根据停留时间和警告次数执行相应操作
        if plate_no in self.special_plates and not self.state_vars["welcome_message_played"]:
            self.tts_manager.start_speak(f"{plate_no},欢迎回家。")
            print("欢迎回家。")
            self.state_vars["welcome_message_played"] = True
            self.state_vars["last_spoken_plate_time"][plate_no] = current_time
        elif plate_no not in self.special_plates:
            if stay_duration > 10 and self.state_vars["warning_repeat_count"] == 0:
                self.tts_manager.start_speak(f"{plate_no},请勿停入专有车位。")
                print(f"{plate_no},请勿停入专有车位。")
                self.state_vars["warning_repeat_count"] = 1
                self.state_vars["last_spoken_plate_time"][plate_no] = current_time
            elif stay_duration > 20 and self.state_vars["warning_repeat_count"] == 1:
                self.tts_manager.start_speak(f"{plate_no},这是第二次警告，请立即离开。")
                print(f"{plate_no},这是第二次警告，请立即离开。")
                self.state_vars["warning_repeat_count"] = 2
                self.state_vars["last_spoken_plate_time"][plate_no] = current_time
            elif stay_duration > 30 and self.state_vars["warning_repeat_count"] == 2:
                self.tts_manager.start_speak(f"{plate_no},这是最后警告，否则将采取措施。")
                print(f"{plate_no},这是最后警告，否则将采取措施。")
                self.state_vars["warning_repeat_count"] = 3
                self.state_vars["last_spoken_plate_time"][plate_no] = current_time
            elif stay_duration > 60 and self.state_vars["warning_repeat_count"] == 3 and not self.state_vars["photo_taken"]:
                image_path = capture_overstaying_vehicle(img0, plate_no)
                self.tts_manager.start_speak(f"{plate_no},违停照片已经记录在案。")
                print(f"{plate_no},违停照片已经记录在案。")
                message = f"警告：陌生车辆 {plate_no} ,长时间违停在您的车位上。"
                send_email("车位异常占用警告", message, image_path)
                content = f'警告：陌生车辆 {plate_no} ,长时间违停在您的车位上。'
                send_sms_smsbao(content)
                self.state_vars["photo_taken"] = True
                self.state_vars["overstay_detected"] = True

    def process_departure(self, current_time):
        for plate, last_seen_time in self.state_vars["last_spoken_plate_time"].items():
            if current_time - last_seen_time > self.DEPARTURE_DELAY:
                if plate in self.special_plates:
                    self.tts_manager.start_speak("祝您一路顺风。")
                    print("祝您一路顺风。")
                    del self.state_vars["last_spoken_plate_time"][plate]
                    break  # 跳出循环，只处理一次
                elif plate not in self.special_plates:
                    self.tts_manager.start_speak("感谢配合，祝您生活愉快。")
                    print("感谢配合，祝您生活愉快。")
                    del self.state_vars["last_spoken_plate_time"][plate]
                    break  # 跳出循环，只处理一次

    def run(self):
        # 设置RTSP URL
        cap = cv2.VideoCapture(self.udp_url)

        if cap.isOpened():
            while True:
                ret_val, img = cap.read()
                result, img0 = self.process_plate_recognition(img)
                ori_img = draw_result(img0, result)
                cv2.imshow("Plate_Rec_Project", ori_img)

                keyCode = cv2.waitKey(30) & 0xFF
                if keyCode == 27:  # ESC键退出
                    break

            cap.release()
            cv2.destroyAllWindows()
        else:
            print("打开直播流失败")

# 主函数
if __name__ == "__main__":
    udp_url = "udp://10.165.138.37:1234"  # 替换为你的UDP流URL
    pr_system = PlateRecognitionSystem(udp_url)
    pr_system.run()