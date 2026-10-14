from flask import Flask, render_template, jsonify, request
import serial
import threading
import time
from datetime import datetime

app = Flask(__name__)

# 아두이노 시리얼 포트 설정 (환경에 맞춰 'COM3', 'COM4' 또는 '/dev/ttyUSB0' 수정)
SERIAL_PORT = 'COM3' 
BAUD_RATE = 9600

data_logs = []

def read_serial():
    global data_logs
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print(f"아두이노 연결 성공 ({SERIAL_PORT})")
        
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    try:
                        parts = line.split(',')
                        if len(parts) == 2:
                            dist = float(parts[0])
                            vib = int(parts[1])
                            
                            # 상태 판별
                            status = "정상"
                            if vib > 15:
                                status = "산사태 심각"
                            elif 0.5 < dist <= 11.0:
                                status = "침수 심각"
                            elif 11.0 < dist <= 13.0:
                                status = "수위 경고"
                            elif 13.0 < dist <= 15.0:
                                status = "수위 주의"
                            elif dist > 15.0:
                                status = "안전"
                            else:
                                status = "미감지"

                            now_time = datetime.now().strftime('%H:%M:%S')
                            
                            log_entry = {
                                "timestamp": now_time,
                                "distance": dist,
                                "vibration": vib,
                                "status": status
                            }
                            
                            data_logs.append(log_entry)
                            # 최근 100개 데이터 유지
                            if len(data_logs) > 100:
                                data_logs.pop(0)
                    except ValueError:
                        pass
            time.sleep(0.1)
    except Exception as e:
        print(f"시리얼 통신 오류: {e}")

# 시리얼 읽기 쓰레드 시작
threading.Thread(target=read_serial, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(data_logs)

@app.route('/clear', methods=['POST'])
def clear_data():
    global data_logs
    data_logs = []
    return jsonify({"message": "모든 기록이 삭제되었습니다."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
