# services/audio.py
import os
import wave
import struct
import math
import threading
import platform
from config import SOUNDS_DIR

try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False

class WavGenerator:
    """Gera arquivos .wav simples via módulo wave nativo do Python.
    Não precisa de biblioteca externa. Executado uma vez ao iniciar."""

    SAMPLE_RATE = 44100

    @staticmethod
    def _sine_samples(freq: float, duration: float, volume: float = 0.4) -> bytes:
        n = int(WavGenerator.SAMPLE_RATE * duration)
        samples = bytearray()
        for i in range(n):
            val = int(volume * 32767 * math.sin(2 * math.pi * freq * i / WavGenerator.SAMPLE_RATE))
            samples += struct.pack('<h', max(-32768, min(32767, val)))
        return bytes(samples)

    @staticmethod
    def _fade(raw: bytes, fade_ms: int = 20) -> bytes:
        """Aplica fade-in e fade-out para evitar clicks."""
        fade_samples = int(WavGenerator.SAMPLE_RATE * fade_ms / 1000)
        arr = bytearray(raw)
        for i in range(min(fade_samples, len(arr) // 2)):
            factor = i / fade_samples
            for offset in (i * 2, len(arr) - (i + 1) * 2):
                if 0 <= offset < len(arr) - 1:
                    val = struct.unpack_from('<h', arr, offset)[0]
                    struct.pack_into('<h', arr, offset, int(val * factor))
        return bytes(arr)

    @classmethod
    def write(cls, filepath: str, notes: list):
        """notes = [(freq_hz, duration_s), ...]"""
        raw = b''.join(cls._fade(cls._sine_samples(f, d)) for f, d in notes)
        with wave.open(filepath, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(cls.SAMPLE_RATE)
            wf.writeframes(raw)

    @classmethod
    def generate_all(cls):
        """Cria os arquivos .wav na pasta sounds/ se não existirem."""
        os.makedirs(SOUNDS_DIR, exist_ok=True)
        files = {
            "start.wav":         [(400, .08), (500, .08), (650, .15)],
            "complete.wav":      [(523, .09), (659, .09), (784, .09), (1047, .22)],
            "break_start.wav":   [(500, .18), (450, .18), (400, .28)],
            "pause.wav":         [(600, .12), (400, .12)],
            "abandon.wav":       [(600, .11), (500, .11), (400, .11), (300, .20)],
            "exhausted.wav":     [(700, .14), (500, .14), (700, .14)],
            "session_done.wav":  [(523, .11), (659, .11), (784, .11), (1047, .14),
                                  (1047, .11), (1319, .11), (1568, .28)],
            "abort.wav":         [(800, .09), (600, .09), (400, .14)],
            "break_warning.wav": [(880, .08), (880, .08), (880, .14)],
            "break_warning_rigid.wav": [(880, .06), (880, .06), (880, .06), (880, .06), (1100, .18)],
            "tick.wav":              [(1000, .04)],
            "resume.wav":            [(400, .08), (600, .12)],
        }
        for name, notes in files.items():
            path = os.path.join(SOUNDS_DIR, name)
            if not os.path.exists(path):
                try:
                    cls.write(path, notes)
                except Exception:
                    pass


class SoundManager:
    """Reproduz sons via playsound (arquivos .wav gerados sinteticamente).
    Fallback para beep de sistema caso playsound não esteja disponível."""

    def __init__(self):
        self.enabled = True
        self.style   = "leve"      
        self.system  = platform.system()
        WavGenerator.generate_all()
        

    # ── utilitários internos ─────────────────────────────────────

    def _play(self, filename: str):
        if not self.enabled:
            return
        path = os.path.join(SOUNDS_DIR, filename)
        if PLAYSOUND_AVAILABLE and os.path.exists(path):
            threading.Thread(target=self._safe_playsound, args=(path,), daemon=True).start()
        else:
            self._fallback_beep(filename)

    @staticmethod
    def _safe_playsound(path: str):
        try:
            playsound(path, block=True)
        except Exception:
            pass

    def _fallback_beep(self, filename: str):
        """Beep de sistema como último recurso."""
        beep_map = {
            "start.wav":        [(400,100),(500,100),(650,150)],
            "complete.wav":     [(523,100),(659,100),(784,100),(1047,250)],
            "break_start.wav":  [(500,200),(450,200),(400,300)],
            "pause.wav":        [(600,120),(400,120)],
            "abandon.wav":      [(600,120),(500,120),(400,120),(300,200)],
            "exhausted.wav":    [(700,150),(500,150),(700,150)],
            "session_done.wav": [(523,120),(659,120),(784,120),(1047,150),
                                 (1047,120),(1319,120),(1568,300)],
            "abort.wav":        [(800,100),(600,100),(400,150)],
            "break_warning.wav":[(880,80),(880,80),(880,140)],
            "tick.wav":         [(1000, 40)],
            "resume.wav":       [(400, 80), (600, 120)],
        }
        notes = beep_map.get(filename, [])
        if not notes:
            return
        def _run():
            for freq, dur in notes:
                try:
                    if self.system == 'Windows':
                        import winsound
                        winsound.Beep(freq, dur)
                    else:
                        sec = dur / 1000.0
                        os.system(f'( speaker-test -t sine -f {freq} >/dev/null 2>&1 '
                                  f'& pid=$! ; sleep {sec} ; kill -9 $pid ) &')
                except Exception:
                    pass
        threading.Thread(target=_run, daemon=True).start()

    # ── API pública ──────────────────────────────────────────────

    def play_task_start(self):      self._play("start.wav")
    def play_pause(self):           self._play("pause.wav")
    def play_break_start(self):     self._play("break_start.wav")
    def play_task_completed(self):  self._play("complete.wav")
    def play_task_abandoned(self):  self._play("abandon.wav")
    def play_time_exhausted(self):  self._play("exhausted.wav")
    def play_session_complete(self):self._play("session_done.wav")
    def play_emergency_abort(self): self._play("abort.wav")
    def play_break_warning(self):   self._play("break_warning.wav")
    def play_break_warning_rigid(self): self._play("break_warning_rigid.wav")
    def play_tick(self):            self._play("tick.wav")
    def play_resume(self):          self._play("resume.wav")