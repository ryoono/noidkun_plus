import sounddevice as sd
import queue
import json
import time
import serial
import winsound
import threading
from vosk import Model, KaldiRecognizer

HOTWORDS = [
    "やばい", "ヤバい", "やば", "やばっ", "ヤバ",
    "危ない", "あぶない", "アブナイ", "あぶなっ", "アブナ", "あぶな",
    "よし", "ヨシ", "良し"
]

DETECT_COOLDOWN = 3.0
FORCE_CUT_INTERVAL = 2.0
sample_rate = 16000
q = queue.Queue()

SERIAL_PORT = "COM6"
BAUD_RATE = 9600
WAV_FILE = "yoshi.wav"  # 再生する音声ファイル

def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

def play_sound_and_notify(ser, stream):
    stream.stop()
    with q.mutex:
        q.queue.clear()
    print("Playing yoshi.wav...")
    winsound.PlaySound(WAV_FILE, winsound.SND_FILENAME)
    print("Sending 'D' to Arduino")
    ser.write(b'D')
    time.sleep(0.1)
    stream.start()

def main():
    model = Model("vosk-model-ja-0.22")
    recognizer = KaldiRecognizer(model, sample_rate)

    print("Listening for hotwords...")
    last_detect_time = 0
    last_cut_time = time.time()

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to Arduino on {SERIAL_PORT}")
    except Exception as e:
        print(f"Error opening serial port: {e}")
        return

    with sd.RawInputStream(samplerate=sample_rate, blocksize=4000, dtype='int16',
                           channels=1, callback=callback) as stream:
        while True:
            try:
                data = q.get(timeout=0.1)
                current_time = time.time()

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "")
                    print(f"[Final] Heard: {text}")
                else:
                    partial_result = json.loads(recognizer.PartialResult())
                    text = partial_result.get("partial", "")
                    print(f"[Partial] Heard: {text}")

                if any(word in text for word in HOTWORDS):
                    if current_time - last_detect_time >= DETECT_COOLDOWN:
                        print("Hotword detected!")
                        last_detect_time = current_time
                        threading.Thread(target=play_sound_and_notify, args=(ser, stream)).start()

                if current_time - last_cut_time >= FORCE_CUT_INTERVAL:
                    final_result = json.loads(recognizer.FinalResult())
                    text = final_result.get("text", "")
                    if text:
                        print(f"[ForceCut Final] Heard: {text}")
                        if any(word in text for word in HOTWORDS):
                            if current_time - last_detect_time >= DETECT_COOLDOWN:
                                print("Hotword detected!")
                                last_detect_time = current_time
                                threading.Thread(target=play_sound_and_notify, args=(ser, stream)).start()
                    last_cut_time = current_time

            except queue.Empty:
                pass

if __name__ == "__main__":
    main()
