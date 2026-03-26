import serial
import json
import time
import math
import random

# com0com에서 설정한 포트 중 '송신'용 포트
GEN_PORT = "COM10" 
BAUDRATE = 230400

def generate_hex_data(count=100):
    """실제 센서처럼 10진수 숫자를 4자리 16진수 문자열로 변환"""
    samples = []
    t = time.time()
    for i in range(count):
        # 사인파 + 노이즈 생성 (0~4095 범위의 12비트 데이터 가정)
        val = int(2048 + 500 * math.sin(t * 5 + i/10) + random.randint(-20, 20))
        val = max(0, min(4095, val)) # 범위 제한
        # 4자리 16진수 문자열로 변환 (예: 2048 -> 0800)
        samples.append(f"{val:04X}")
    return "".join(samples)

def main():
    try:
        ser = serial.Serial(GEN_PORT, BAUDRATE, timeout=1)
        print(f"[OK] Generator started on {GEN_PORT}")
        
        seq_num = 0
        while True:
            # 1. 가짜 데이터 생성
            hex_payload = generate_hex_data(80) # 한 번에 80개 샘플 전송
            
            # 2. 실제 장비의 JSON 포맷 구성
            data_obj = {
                "sensorData": hex_payload,
                "seq": f"{seq_num:02X}", # 16진수 시퀀스 번호
                "tick": int(time.time() * 1000) % 0xFFFF
            }
            
            # 3. JSON 직렬화 후 전송 (끝에 \r\n 필수)
            json_str = json.dumps(data_obj) + "\r\n"
            ser.write(json_str.encode("utf-8"))
            
            print(f"[SEND] Seq: {seq_num}, Data Length: {len(hex_payload)}")
            
            seq_num = (seq_num + 1) % 256
            time.sleep(0.1) # 10Hz 주기로 전송

    except serial.SerialException as e:
        print(f"[Error] 포트를 열 수 없습니다: {e}")
    except KeyboardInterrupt:
        print("\n[Stop] 생성기를 중단합니다.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()