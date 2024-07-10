import os
import asyncio
import edge_tts
import pygame
import tempfile
import threading
from threading import Lock

class TTSManager:
    def __init__(self):
        self.lock = Lock()
        # 初始化 pygame
        pygame.init()
        pygame.mixer.init()
    
    # 初始化TTS引擎
    async def speak(self, text, voice):
        with self.lock:  # 获取锁
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                output_file = temp_file.name

            # 使用 edge-tts 生成语音并保存到临时文件
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_file)

            # 使用 pygame 播放音频
            pygame.mixer.music.load(output_file)
            pygame.mixer.music.play()

            # 等待播放完成
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            # 删除临时文件
            os.remove(output_file)
            # 释放锁（锁将在此代码块结束时自动释放）

    def start_speak(self, text, voice="zh-CN-XiaoxiaoNeural"):
        # 在一个新线程中运行 speak 方法
        threading.Thread(target=lambda: asyncio.run(self.speak(text, voice))).start()