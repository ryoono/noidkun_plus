import sounddevice as sd
import queue
import json
import time
from vosk import Model, KaldiRecognizer

# 複数ホットワード（表記ゆれ含む）
HOTWORDS = [
    "やばい", "ヤバい", "やば", "やばっ", "ヤバ",
    "危ない", "あぶない", "アブナイ", "あぶなっ", "アブナ", "あぶな"
]

# 多重出力抑制の待機秒数（必要に応じて変更可能）
DETECT_COOLDOWN = 3.0  # 秒

sample_rate = 16000
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

def main():
    model = Model("vosk-model-ja-0.22")  # モデルフォルダを指定
    recognizer = KaldiRecognizer(model, sample_rate)

    print("Listening for hotwords...")
    last_detect_time = 0  # 最後に検出した時間を記録

    with sd.RawInputStream(samplerate=sample_rate, blocksize=4000, dtype='int16',
                           channels=1, callback=callback):
        while True:
            data = q.get()
            text = ""

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                print(f"[Final] Heard: {text}")
            else:
                partial_result = json.loads(recognizer.PartialResult())
                text = partial_result.get("partial", "")
                print(f"[Partial] Heard: {text}")

            # ホットワード検出 & クールダウン確認
            current_time = time.time()
            if any(word in text for word in HOTWORDS):
                if current_time - last_detect_time >= DETECT_COOLDOWN:
                    print("detect")
                    last_detect_time = current_time  # 検出時間を更新

if __name__ == "__main__":
    main()
