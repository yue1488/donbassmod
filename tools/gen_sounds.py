"""Procedural sound effects for the Donbass mod: synthesises WAV with numpy, encodes OGG Vorbis with ffmpeg
and writes assets/donbass/sounds.json.  Deterministic (fixed seeds).  Needs numpy and ffmpeg (libvorbis).

Sound events are described in SOUNDS below; ModSounds.java registers the same names (validate.py cross-checks).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import wave

try:
    import numpy as np
except ImportError:          # validate.py imports this module only for the subtitle texts (no numpy needed there)
    np = None

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "src", "main", "resources", "assets", "donbass")
SOUND_DIR = os.path.join(ASSETS, "sounds")
SR = 32000
N = "donbass:"


# ------------------------------------------------------------ primitives ----
def t_axis(dur):
    return np.arange(int(SR * dur)) / SR


def env_exp(t, tau):
    return np.exp(-t / tau)


def fft_filter(x, lo=None, hi=None, smooth=0.15):
    """Band-limit with a soft-edged FFT mask (lo/hi in Hz, either may be None)."""
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1.0 / SR)
    mask = np.ones_like(freqs)
    if lo is not None:
        mask *= 1.0 / (1.0 + np.exp(-(freqs - lo) / max(lo * smooth, 1.0)))
    if hi is not None:
        mask *= 1.0 / (1.0 + np.exp((freqs - hi) / max(hi * smooth, 1.0)))
    return np.fft.irfft(spec * mask, n=len(x))


def formants(x, centres, width=0.18, gains=None):
    """Impose vocal-tract resonances on a source signal (frequency-domain bumps)."""
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1.0 / SR)
    resp = np.full_like(freqs, 0.04)
    for i, c in enumerate(centres):
        g = 1.0 if gains is None else gains[i]
        resp += g * np.exp(-0.5 * ((freqs - c) / (c * width)) ** 2)
    return np.fft.irfft(spec * resp, n=len(x))


def normalise(x, peak=0.9):
    m = float(np.max(np.abs(x))) or 1.0
    return x / m * peak


def fade(x, ms_in=2, ms_out=12):
    n_in, n_out = int(SR * ms_in / 1000), int(SR * ms_out / 1000)
    x = x.copy()
    if n_in:
        x[:n_in] *= np.linspace(0, 1, n_in)
    if n_out:
        x[-n_out:] *= np.linspace(1, 0, n_out)
    return x


def echo(x, delays_ms, gains):
    out = x.copy()
    for d, g in zip(delays_ms, gains):
        n = int(SR * d / 1000)
        out[n:] += x[:-n] * g
    return out


def glottal(f0_curve, rng, jitter=0.012):
    """Sawtooth-like glottal pulse train following a per-sample f0 curve (Hz)."""
    f = f0_curve * (1.0 + jitter * rng.standard_normal(len(f0_curve)))
    phase = np.cumsum(f) / SR
    saw = 2.0 * (phase - np.floor(phase)) - 1.0
    return saw + 0.25 * np.sin(2 * np.pi * phase)


# ------------------------------------------------------------- gun sounds ----
def ak_shot(seed, pitch=1.0):
    rng = np.random.default_rng(seed)
    t = t_axis(0.55)
    crack = rng.standard_normal(len(t)) * env_exp(t, 0.012)
    crack = fft_filter(crack, lo=600)
    body = rng.standard_normal(len(t)) * env_exp(t, 0.045)
    body = fft_filter(body, lo=120, hi=2600)
    f = 150.0 * pitch * np.exp(-t * 14.0) + 48.0
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(t, 0.09)
    tail = rng.standard_normal(len(t)) * env_exp(t, 0.16) * 0.35
    tail = fft_filter(tail, lo=90, hi=1500)
    x = 0.9 * crack + 0.9 * body + 1.1 * boom + tail
    x = echo(x, [38, 95, 170], [0.28, 0.16, 0.08])
    x = np.tanh(1.8 * x)
    return fade(normalise(x), 1, 40)


def ak_empty():
    rng = np.random.default_rng(11)
    t = t_axis(0.16)
    click = rng.standard_normal(len(t)) * env_exp(t, 0.004)
    click = fft_filter(click, lo=1500, hi=7000)
    ping = np.sin(2 * np.pi * 2300 * t) * env_exp(t, 0.01) * 0.3
    return fade(normalise(click + ping, 0.7), 1, 20)


def metal_click(rng, dur=0.08, centre=3200, tau=0.006):
    t = t_axis(dur)
    n = rng.standard_normal(len(t)) * env_exp(t, tau)
    n = fft_filter(n, lo=centre * 0.5, hi=centre * 2.2)
    ring = np.sin(2 * np.pi * centre * t) * env_exp(t, tau * 1.6) * 0.5
    return n + ring


def ak_reload():
    rng = np.random.default_rng(23)
    out = np.zeros(int(SR * 1.9))

    def put(sig, at, gain=1.0):
        i = int(SR * at)
        out[i:i + len(sig)] += sig[: len(out) - i] * gain

    put(metal_click(rng, 0.10, 2600, 0.008), 0.05, 0.9)                    # magazine release
    t = t_axis(0.22)
    slide = fft_filter(rng.standard_normal(len(t)), lo=300, hi=3000) * np.linspace(1, 0.1, len(t)) * 0.35
    put(slide, 0.18, 0.8)                                                 # magazine drops out
    t = t_axis(0.35)
    rustle = fft_filter(rng.standard_normal(len(t)), lo=500, hi=2500) * (np.sin(np.pi * t / 0.35) ** 2) * 0.18
    put(rustle, 0.55, 0.9)                                                # fumbling for a new one
    put(metal_click(rng, 0.12, 1900, 0.012), 1.0, 1.0)                    # magazine seats
    put(metal_click(rng, 0.10, 3400, 0.006), 1.28, 0.8)
    t = t_axis(0.12)
    put(fft_filter(rng.standard_normal(len(t)), lo=200, hi=2000) * env_exp(t, 0.03) * 0.8, 1.55, 0.9)  # bolt forward
    return fade(normalise(out, 0.8), 2, 30)


# --------------------------------------------------------------- voices ----
def voice(dur, f0_start, f0_end, centres, seed, breathy=0.12, shape=2.0, attack=0.04, width=0.16, vibrato=0.0):
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    curve = f0_start + (f0_end - f0_start) * (t / dur) ** shape
    if vibrato:
        curve = curve * (1 + vibrato * np.sin(2 * np.pi * 6.0 * t))
    src = glottal(curve, rng)
    src += breathy * rng.standard_normal(len(t))
    x = formants(src, centres, width=width)
    amp = np.minimum(1.0, t / attack) * np.minimum(1.0, (dur - t) / 0.08)
    return fade(normalise(x * amp, 0.85), 3, 25)


def militia_ambient(seed):          # low gruff "hm"
    return voice(0.55, 105, 92, [480, 1250, 2400], seed, breathy=0.22, attack=0.08)


def militia_hurt():                 # short sharp grunt
    return voice(0.32, 190, 110, [720, 1250, 2500], 31, breathy=0.2, shape=1.2, attack=0.015)


def militia_death():                # long falling groan
    return voice(0.95, 150, 52, [620, 1100, 2300], 37, breathy=0.3, shape=1.0, attack=0.03)


def miner_ambient(seed):            # villager-like mumble "hrm"
    return voice(0.6, 128, 142, [420, 1080, 2200], seed, breathy=0.14, attack=0.1, width=0.12, vibrato=0.02)


def miner_hurt():
    return voice(0.38, 210, 130, [650, 1350, 2500], 41, breathy=0.18, shape=1.1, attack=0.015)


def miner_death():
    return voice(0.9, 165, 60, [540, 980, 2300], 43, breathy=0.28, shape=1.0, attack=0.03)


def miner_yes():                    # rising two-note "hm-HM"
    a = voice(0.2, 125, 135, [430, 1100, 2300], 51, attack=0.03, width=0.12)
    b = voice(0.3, 160, 190, [470, 1150, 2300], 52, attack=0.03, width=0.12, shape=1.0)
    return np.concatenate([a, np.zeros(int(SR * 0.04)), b])


def miner_no():                     # falling "uh-uh"
    a = voice(0.2, 150, 118, [520, 1020, 2300], 53, attack=0.02, width=0.12)
    b = voice(0.28, 135, 95, [480, 980, 2300], 54, attack=0.02, width=0.12, shape=1.0)
    return np.concatenate([a, np.zeros(int(SR * 0.05)), b])


def armor_set():                    # clank of the full coal armour set bonus
    rng = np.random.default_rng(61)
    t = t_axis(0.6)
    x = np.zeros(len(t))
    for f, at in ((330, 0.0), (495, 0.05), (660, 0.1)):
        i = int(SR * at)
        seg = np.sin(2 * np.pi * f * t[: len(t) - i]) * env_exp(t[: len(t) - i], 0.18)
        x[i:] += seg
    x += fft_filter(rng.standard_normal(len(t)) * env_exp(t, 0.01), lo=800) * 0.4
    return fade(normalise(x, 0.7), 2, 60)


# ------------------------------------------------------------- the boss ----
def director_ambient(seed):         # a slow, tired growl
    return voice(0.8, 88, 72, [420, 980, 2200], seed, breathy=0.25, attack=0.12, vibrato=0.01)


def director_hurt():
    return voice(0.32, 150, 105, [560, 1300, 2500], 91, breathy=0.2, shape=1.2, attack=0.02)


def director_death():               # a long fall into silence
    return voice(2.2, 110, 38, [380, 900, 2000], 92, breathy=0.3, shape=1.6, attack=0.1, vibrato=0.03)


def director_roar():                # phase change: a roar that swells and breaks
    rng = np.random.default_rng(93)
    dur = 1.9
    t = t_axis(dur)
    curve = 75 + 70 * np.sin(np.pi * np.minimum(t / dur, 1.0)) ** 1.5 - 18 * (t / dur)
    curve = curve * (1 + 0.02 * np.sin(2 * np.pi * 9.0 * t))
    src = glottal(curve, rng, jitter=0.03) + 0.35 * rng.standard_normal(len(t))
    x = formants(src, [520, 1100, 2400], width=0.2)
    amp = np.minimum(1.0, t / 0.25) * np.minimum(1.0, (dur - t) / 0.4)
    return fade(normalise(np.tanh(2.4 * normalise(x * amp)), 0.9), 3, 60)


def director_slam():                # sledgehammer on the floor: boom, crack, falling rubble
    rng = np.random.default_rng(94)
    t = t_axis(1.1)
    f = 110.0 * np.exp(-t * 9.0) + 36.0
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(t, 0.22)
    crack = fft_filter(rng.standard_normal(len(t)) * env_exp(t, 0.02), lo=400, hi=5000)
    rumble = fft_filter(rng.standard_normal(len(t)) * env_exp(t, 0.35), lo=40, hi=420) * 0.9
    rubble = np.zeros(len(t))
    for at in (0.12, 0.2, 0.33, 0.41, 0.58):
        i = int(SR * at)
        seg = fft_filter(rng.standard_normal(int(SR * 0.05)), lo=800, hi=4200) * env_exp(t_axis(0.05), 0.012)
        rubble[i:i + len(seg)] += seg * 0.5
    x = 1.3 * boom + 0.9 * crack + rumble + rubble
    return fade(normalise(np.tanh(1.6 * x), 0.9), 1, 80)


def director_siren():               # factory hooter: two rising-falling wails
    t = t_axis(3.0)
    wail = 430 + 190 * np.sin(np.pi * np.minimum(t / 1.5, 1.0)) ** 2 * (t < 1.5) + \
        190 * np.sin(np.pi * np.clip((t - 1.5) / 1.5, 0.0, 1.0)) ** 2 * (t >= 1.5)
    ph = np.cumsum(wail) / SR
    x = sum(np.sin(2 * np.pi * ph * k) / k for k in (1, 2, 3, 4, 5))
    x = fft_filter(x, lo=150, hi=3000)
    x = echo(x, [180, 420], [0.35, 0.18])
    amp = np.minimum(1.0, t / 0.08) * np.minimum(1.0, (3.0 - t) / 0.5)
    return fade(normalise(x * amp, 0.85), 3, 100)


# Boss music: three 16 s loops (MUSIC_LOOP_TICKS in CombineDirectorEntity is 320 = 16 s).
MUSIC_SECONDS = 16.0


def _saw_wave(freq, t):
    ph = (freq * t) % 1.0
    return 2.0 * ph - 1.0


def _place(out, sig, at, gain=1.0):
    i = int(SR * at)
    if i >= len(out):
        return
    n = min(len(sig), len(out) - i)
    out[i:i + n] += sig[:n] * gain


def _kick(tau=0.11):
    t = t_axis(0.35)
    f = 130.0 * np.exp(-t * 22.0) + 42.0
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(t, tau)


def _hat(rng, tau=0.025):
    t = t_axis(0.12)
    return fft_filter(rng.standard_normal(len(t)) * env_exp(t, tau), lo=6000) * 0.5


def _anvil(freq):
    t = t_axis(0.9)
    x = sum(np.sin(2 * np.pi * freq * m * t) * env_exp(t, 0.5 / m) / m for m in (1.0, 2.76, 5.4))
    return x + fft_filter(np.random.default_rng(5).standard_normal(len(t)) * env_exp(t, 0.01), lo=1500) * 0.5


def _pad(freqs, dur, detune=0.004, lo=None, hi=900):
    t = t_axis(dur)
    x = sum(_saw_wave(f * (1 + d), t) for f in freqs for d in (-detune, 0.0, detune))
    return fft_filter(x, lo=lo, hi=hi) / (3 * len(freqs))


def music(phase):
    rng = np.random.default_rng(200 + phase)
    out = np.zeros(int(SR * MUSIC_SECONDS))
    A1, E2, A2, C3, Eb3 = 55.0, 82.41, 110.0, 130.81, 155.56
    if phase == 1:                                    # slow, heavy: drone, anvil on every second beat
        _place(out, _pad([A1, E2, A2], MUSIC_SECONDS, hi=700), 0.0, 0.9)
        beat = 60.0 / 72.0
        k = 0
        while k * beat < MUSIC_SECONDS - 0.5:
            _place(out, _kick(), k * beat, 0.9 if k % 2 == 0 else 0.5)
            if k % 4 == 3:
                _place(out, _anvil(196.0), k * beat + beat / 2, 0.45)
            k += 1
        for bar in range(0, 8):                       # a minor-third swell every two seconds
            _place(out, _pad([A2, C3], 2.0, hi=1100) * np.sin(np.linspace(0, np.pi, int(SR * 2.0))) ** 2,
                   bar * 2.0, 0.55)
    elif phase == 2:                                  # faster: driving kick, off-beat hats, bass ostinato
        beat = 60.0 / 112.0
        _place(out, _pad([A1, E2], MUSIC_SECONDS, hi=600), 0.0, 0.6)
        for k in range(int(MUSIC_SECONDS / beat) - 1):
            _place(out, _kick(), k * beat, 0.95)
            _place(out, _hat(rng), k * beat + beat / 2, 0.55)
            note = (A1, A1, C3 / 2, A1, E2, A1, C3 / 2, E2)[k % 8]
            t = t_axis(beat * 0.9)
            bass = fft_filter(_saw_wave(note, t), hi=420) * env_exp(t, 0.35)
            _place(out, bass, k * beat + beat / 2, 0.7)
            if k % 8 == 4:
                _place(out, _anvil(220.0), k * beat, 0.5)
        for bar in range(0, 7):                       # brass-like stabs on the bar line
            _place(out, _pad([A2, C3, E2 * 3], 0.9, hi=1800) * env_exp(t_axis(0.9), 0.35), bar * 8 * beat + 0.02, 0.7)
    else:                                             # frantic: double-time kick, distorted bass, tritone stabs
        beat = 60.0 / 150.0
        _place(out, _pad([A1, Eb3 / 2], MUSIC_SECONDS, detune=0.01, hi=800), 0.0, 0.7)
        for k in range(int(MUSIC_SECONDS / beat) - 1):
            _place(out, _kick(0.09), k * beat, 1.0)
            if k % 2:
                _place(out, _hat(rng, 0.02), k * beat + beat / 2, 0.6)
            note = (A1, A1, Eb3 / 2, A1, A1, E2, Eb3 / 2, A1)[k % 8]
            t = t_axis(beat * 0.95)
            bass = np.tanh(3.0 * fft_filter(_saw_wave(note, t), hi=520)) * env_exp(t, 0.3)
            _place(out, bass, k * beat + beat / 2, 0.6)
            if k % 4 == 0:
                _place(out, _anvil(165.0), k * beat + beat / 4, 0.4)
        for bar in range(0, 10):                      # a rising siren-like line over the top
            t = t_axis(1.5)
            line = np.sin(2 * np.pi * np.cumsum(330 + 220 * (t / 1.5) ** 2) / SR) * np.sin(np.pi * t / 1.5)
            _place(out, line, bar * 1.6, 0.18)
    out = np.tanh(1.3 * normalise(out, 0.95))
    return fade(normalise(out, 0.8), 40, 400)


# --------------------------------------------------------------- registry ----
# event name -> (subtitle_key, subtitle (en, ru, pl), category, [(file, generator), ...])
SOUNDS = {
    "item.ak_shot": ("Rifle fires", "Автомат стреляет", "Karabin strzela", "player",
                     [("ak_shot_1", lambda: ak_shot(101, 1.0)), ("ak_shot_2", lambda: ak_shot(102, 1.12))]),
    "item.ak_reload": ("Rifle reloads", "Перезарядка автомата", "Przeładowanie karabinu", "player",
                       [("ak_reload", ak_reload)]),
    "item.ak_empty": ("Rifle clicks", "Щелчок автомата", "Kliknięcie karabinu", "player", [("ak_empty", ak_empty)]),
    "armor.coal_set": ("Coal armour clanks", "Звякает угольная броня", "Brzęk zbroi węglowej", "player",
                       [("coal_set", armor_set)]),
    "entity.militia.ambient": ("Fighter mutters", "Боец бормочет", "Bojownik mruczy", "hostile",
                               [("militia_ambient_1", lambda: militia_ambient(71)),
                                ("militia_ambient_2", lambda: militia_ambient(72))]),
    "entity.militia.hurt": ("Fighter grunts", "Боец хрипит", "Bojownik stęka", "hostile", [("militia_hurt", militia_hurt)]),
    "entity.militia.death": ("Fighter dies", "Боец умирает", "Bojownik umiera", "hostile", [("militia_death", militia_death)]),
    "entity.miner.ambient": ("Miner mumbles", "Шахтёр бормочет", "Górnik mruczy", "neutral",
                             [("miner_ambient_1", lambda: miner_ambient(81)),
                              ("miner_ambient_2", lambda: miner_ambient(82))]),
    "entity.miner.hurt": ("Miner hurts", "Шахтёр ранен", "Górnik jest ranny", "neutral", [("miner_hurt", miner_hurt)]),
    "entity.miner.death": ("Miner dies", "Шахтёр умирает", "Górnik umiera", "neutral", [("miner_death", miner_death)]),
    "entity.miner.yes": ("Miner agrees", "Шахтёр соглашается", "Górnik się zgadza", "neutral", [("miner_yes", miner_yes)]),
    "entity.miner.no": ("Miner refuses", "Шахтёр отказывает", "Górnik odmawia", "neutral", [("miner_no", miner_no)]),
    "entity.director.ambient": ("The Chairman growls", "Председатель рычит", "Przewodniczący warczy", "hostile",
                                [("director_ambient_1", lambda: director_ambient(95)),
                                 ("director_ambient_2", lambda: director_ambient(96))]),
    "entity.director.hurt": ("The Chairman grunts", "Председатель хрипит", "Przewodniczący stęka", "hostile",
                             [("director_hurt", director_hurt)]),
    "entity.director.death": ("The Chairman falls", "Председатель падает", "Przewodniczący upada", "hostile",
                              [("director_death", director_death)]),
    "entity.director.roar": ("The Chairman roars", "Председатель ревёт", "Przewodniczący ryczy", "hostile",
                             [("director_roar", director_roar)]),
    "entity.director.slam": ("The Chairman slams the ground", "Председатель бьёт по земле", "Przewodniczący uderza w ziemię",
                             "hostile", [("director_slam", director_slam)]),
    "item.director_siren": ("Factory siren wails", "Воет сирена комбината", "Syrena kombinatu wyje", "player",
                            [("director_siren", director_siren)]),
    "music.director.phase1": (None, None, None, "music", [("music_director_1", lambda: music(1))]),
    "music.director.phase2": (None, None, None, "music", [("music_director_2", lambda: music(2))]),
    "music.director.phase3": (None, None, None, "music", [("music_director_3", lambda: music(3))]),
}


def subtitle_key(event):
    return "subtitles." + "donbass." + event


def write_wav(path, x):
    pcm = np.clip(x, -1.0, 1.0)
    pcm = (pcm * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def encode(wav, ogg):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-c:a", "libvorbis", "-q:a", "4", ogg],
                   check=True)


def lang_entries():
    """subtitle key -> (en, ru, pl); consumed by gen_resources.gen_lang through content.LANG_EXTRA."""
    return {subtitle_key(e): (v[0], v[1], v[2]) for e, v in SOUNDS.items() if v[0]}


def main():
    if np is None:
        sys.exit("numpy is required to synthesise the sounds (pip install numpy)")
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg with libvorbis is required to build the OGG files")
    shutil.rmtree(SOUND_DIR, ignore_errors=True)
    os.makedirs(SOUND_DIR)
    sounds_json = {}
    total = 0
    with tempfile.TemporaryDirectory() as tmp:
        for event, (_en, _ru, _pl, category, files) in SOUNDS.items():
            names = []
            for fname, gen in files:
                wav = os.path.join(tmp, fname + ".wav")
                write_wav(wav, gen())
                encode(wav, os.path.join(SOUND_DIR, fname + ".ogg"))
                names.append({"name": N + fname, "stream": True} if event.startswith("music.") else N + fname)
                total += 1
            sounds_json[event] = {"sounds": names}
            if _en:
                sounds_json[event]["subtitle"] = subtitle_key(event)
    with open(os.path.join(ASSETS, "sounds.json"), "w", encoding="utf-8") as f:
        json.dump(sounds_json, f, indent=2, ensure_ascii=False)
        f.write("\n")
    size = sum(os.path.getsize(os.path.join(SOUND_DIR, n)) for n in os.listdir(SOUND_DIR))
    print(f"sounds: {len(SOUNDS)} events, {total} ogg files, {size // 1024} KiB")


if __name__ == "__main__":
    main()
