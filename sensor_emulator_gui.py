import serial
import json
import time
import math
import random
import threading
import tkinter as tk
from tkinter import ttk

# 설정
GEN_PORT = "COM10"
BAUDRATE = 230400

class SensorEmulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("IoT Sensor Simulator")
        self.root.geometry("300x250")
        
        self.running = False
        self.mode = "piezo"  # 기본 모드
        self.ser = None
        
        # UI 구성
        ttk.Label(root, text="Sensor Data Simulator", font=('Arial', 14, 'bold')).pack(pady=10)
        
        self.status_label = ttk.Label(root, text=f"Port: {GEN_PORT} - Disconnected", foreground="red")
        self.status_label.pack(pady=5)
        
        self.mode_label = ttk.Label(root, text=f"Current Mode: {self.mode.upper()}", font=('Arial', 10))
        self.mode_label.pack(pady=5)

        # 버튼들
        ttk.Button(root, text="Switch to PIEZO", command=lambda: self.set_mode("piezo")).pack(fill='x', padx=20, pady=2)
        ttk.Button(root, text="Switch to ADXL (X-Axis)", command=lambda: self.set_mode("adxl")).pack(fill='x', padx=20, pady=2)
        
        self.start_btn = ttk.Button(root, text="START SENDING", command=self.toggle_running)
        self.start_btn.pack(fill='x', padx=20, pady=15)

    def set_mode(self, mode):
        self.mode = mode
        self.mode_label.config(text=f"Current Mode: {self.mode.upper()}")
        print(f"[MODE CHANGED] {self.mode}")

    def toggle_running(self):
        if not self.running:
            try:
                self.ser = serial.Serial(GEN_PORT, BAUDRATE, timeout=1)
                self.running = True
                self.start_btn.config(text="STOP SENDING")
                self.status_label.config(text=f"Port: {GEN_PORT} - Connected", foreground="green")
                threading.Thread(target=self.send_loop, daemon=True).start()
            except Exception as e:
                self.status_label.config(text=f"Error: {e}", foreground="red")
        else:
            self.running = False
            self.start_btn.config(text="START SENDING")
            self.status_label.config(text=f"Port: {GEN_PORT} - Disconnected", foreground="red")
            if self.ser:
                self.ser.close()

    # 🔥 수정된 부분: num_samples 인자를 받을 수 있게 수정
    def generate_hex_payload(self, num_samples=80):
        """가짜 16진수 데이터 생성"""
        samples = []
        t = time.time()
        for i in range(num_samples):
            # 모드에 따라 파형 주파수 조절
            freq = 5 if self.mode == "piezo" else 2
            val = int(2048 + 500 * math.sin(t * freq + i/10) + random.randint(-20, 20))
            val = max(0, min(4095, val))
            samples.append(f"{val:04X}")
        return "".join(samples)

    def send_loop(self):
        print("[INFO] Optimized loop started (1Hz)")
        while self.running:
            # 30초 주기에 대응하기 위해 한 번에 100개씩 뭉쳐서 보냄
            samples_per_batch = 100 
            
            # 16: ADXL_X 축 (프론트엔드 기본 설정 "x"에 맞춤)
            target_seq = 0 if self.mode == "piezo" else 16 
            
            # 🔥 generate_hex_payload에 인자 전달
            hex_data = self.generate_hex_payload(samples_per_batch)
            
            data_obj = {
                "sensorData": hex_data,
                "seq": f"{target_seq:02X}",
                "tick": int(time.time() * 1000) % 0xFFFF
            }
            
            try:
                # 1초에 한 번 전송 (서버 부하 감소)
                self.ser.write((json.dumps(data_obj) + "\r\n").encode())
                print(f"[SEND] Mode: {self.mode}, Samples: {samples_per_batch}")
                time.sleep(1.0) 
            except Exception as e:
                print(f"[ERROR] {e}")
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = SensorEmulatorGUI(root)
    root.mainloop()