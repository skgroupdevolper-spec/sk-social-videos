#!/usr/bin/env python3
"""Offline English voiceover for SK Developer videos.

Piper voice en_US-libritts_r-medium run with onnxruntime. espeak-ng is not available in the sandbox,
so phonemes come from the CMU Pronouncing Dictionary (ARPAbet -> espeak-style IPA) plus a small
brand/tech lexicon below. Fetch the model first: bash tools/voice/fetch_model.sh

  python3 tools/voice/tts.py "Text to say." out.wav [--speaker 0] [--speed 1.0]
"""
import os, re, sys, json, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(HERE, "models")
MODEL = os.path.join(MD, "en_US-libritts_r-medium.onnx")

V = {"AA": "ɑː", "AE": "æ", "AH": "ʌ", "AO": "ɔː", "AW": "aʊ", "AY": "aɪ", "EH": "ɛ", "ER": "ɜː", "EY": "eɪ",
     "IH": "ɪ", "IY": "iː", "OW": "oʊ", "OY": "ɔɪ", "UH": "ʊ", "UW": "uː"}
V0 = {"AH": "ə", "ER": "ɚ", "IY": "i", "IH": "ɪ", "UW": "u"}
C = {"B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "F": "f", "G": "ɡ", "HH": "h", "JH": "dʒ", "K": "k", "L": "l",
     "M": "m", "N": "n", "NG": "ŋ", "P": "p", "R": "ɹ", "S": "s", "SH": "ʃ", "T": "t", "TH": "θ", "V": "v",
     "W": "w", "Y": "j", "Z": "z", "ZH": "ʒ"}
LETTER = {"a": "ˈeɪ", "b": "bˈiː", "c": "sˈiː", "d": "dˈiː", "e": "ˈiː", "f": "ˈɛf", "g": "dʒˈiː", "h": "ˈeɪtʃ",
          "i": "ˈaɪ", "j": "dʒˈeɪ", "k": "kˈeɪ", "l": "ˈɛl", "m": "ˈɛm", "n": "ˈɛn", "o": "ˈoʊ", "p": "pˈiː",
          "q": "kjˈuː", "r": "ˈɑːɹ", "s": "ˈɛs", "t": "tˈiː", "u": "jˈuː", "v": "vˈiː", "w": "dˈʌbəljuː",
          "x": "ˈɛks", "y": "wˈaɪ", "z": "zˈiː"}
# words CMUdict lacks or says badly (lower-case keys, ARPAbet or raw IPA starting with '/')
LEX = {
    "whatsapp": "W AH1 T S AE2 P", "shopify": "SH AA1 P IH0 F AY2", "woocommerce": "W UW1 K AA2 M ER0 S",
    "wordpress": "W ER1 D P R EH2 S", "javascript": "JH AA1 V AH0 S K R IH2 P T", "chatbot": "CH AE1 T B AA2 T",
    "chatbots": "CH AE1 T B AA2 T S", "ecommerce": "IY1 K AA2 M ER0 S", "eCommerce": "IY1 K AA2 M ER0 S",
    "nextjs": "N EH1 K S T JH EY1 EH1 S", "reactjs": "R IY0 AE1 K T JH EY1 EH1 S", "nodejs": "N OW1 D JH EY1 EH1 S",
    "webhook": "W EH1 B HH UH2 K", "webhooks": "W EH1 B HH UH2 K S", "frontend": "F R AH1 N T EH2 N D",
    "backend": "B AE1 K EH2 N D", "fullstack": "F UH1 L S T AE2 K", "dashboards": "D AE1 SH B AO2 R D Z",
    "plugins": "P L AH1 G IH0 N Z", "signup": "S AY1 N AH2 P", "checkout": "CH EH1 K AW2 T", "onboarding": "AA1 N B AO2 R D IH0 NG",
    "workflow": "W ER1 K F L OW2", "workflows": "W ER1 K F L OW2 Z", "app": "AE1 P", "apps": "AE1 P S",
    "online": "AO1 N L AY2 N", "website": "W EH1 B S AY2 T", "websites": "W EH1 B S AY2 T S", "laravel": "L AE1 R AH0 V EH2 L",
    "flutter": "F L AH1 T ER0", "sk": "/ˈɛs kˈeɪ", "ai": "/ˈeɪ ˈaɪ", "api": "/ˈeɪ pˈiː ˈaɪ", "apis": "/ˈeɪ pˈiː ˈaɪz",
    "crm": "/sˈiː ˈɑːɹ ˈɛm", "erp": "/ˈiː ˈɑːɹ pˈiː", "ui": "/jˈuː ˈaɪ", "ux": "/jˈuː ˈɛks", "seo": "/ˈɛs ˈiː ˈoʊ",
    "mvp": "/ˈɛm vˈiː pˈiː", "saas": "/sˈæs", "php": "/pˈiː ˈeɪtʃ pˈiː", "html": "/ˈeɪtʃ tˈiː ˈɛm ˈɛl", "css": "/sˈiː ˈɛs ˈɛs",
}
_dict = None
def cmu():
    global _dict
    if _dict is None:
        _dict = {}
        for line in open(os.path.join(MD, "cmudict.dict"), encoding="utf-8"):
            p = line.split("#")[0].split()
            if not p: continue
            w = re.sub(r"\(\d+\)$", "", p[0])
            _dict.setdefault(w, " ".join(p[1:]))
    return _dict

def arpa2ipa(arpa):
    out = []
    for ph in arpa.split():
        m = re.match(r"([A-Z]+)([012])?$", ph)
        b, st = m.group(1), m.group(2)
        if b in V:
            if st == "1": out.append("ˈ" + V[b])
            elif st == "2": out.append("ˌ" + V[b])
            else: out.append(V0.get(b, V[b]))
        else: out.append(C[b])
    return "".join(out)

def word_ipa(w):
    lw = w.lower()
    if lw in LEX:
        v = LEX[lw]; return v[1:] if v.startswith("/") else arpa2ipa(v)
    if w.isupper() and len(w) <= 4 and w.isalpha(): return " ".join(LETTER[c] for c in lw)
    d = cmu()
    if lw in d: return arpa2ipa(d[lw])
    if lw.endswith("'s") and lw[:-2] in d: return arpa2ipa(d[lw[:-2]]) + "z"
    for suf, add in (("s", "z"), ("es", "ᵻz"), ("ed", "d"), ("ing", "ɪŋ"), ("ly", "li")):
        if lw.endswith(suf) and lw[:-len(suf)] in d: return arpa2ipa(d[lw[:-len(suf)]]) + add
    if "-" in lw: return " ".join(word_ipa(x) for x in lw.split("-") if x)
    sys.stderr.write(f"[tts] unknown word spelled out: {w}\n")
    return " ".join(LETTER.get(c, "") for c in lw if c.isalpha())

def phonemize(text):
    text = text.replace("—", ", ").replace("–", ", ").replace("&", " and ").replace("/", " ").replace("…", ".")
    text = re.sub(r"\bE-?commerce\b", "ecommerce", text, flags=re.I)
    text = re.sub(r"(\w)\.js\b", r"\1js", text)
    out = []
    for tok in re.findall(r"[A-Za-z][A-Za-z'\-]*|[.,!?;:]", text):
        if tok in ".,!?;:": out.append(tok)
        else: out.append(" " + word_ipa(tok))
    s = "".join(out).strip()
    return re.sub(r"\s+", " ", s)

class Voice:
    def __init__(self):
        import onnxruntime as ort
        self.cfg = json.load(open(MODEL + ".json"))
        self.idmap = self.cfg["phoneme_id_map"]
        o = ort.SessionOptions(); o.log_severity_level = 3
        self.sess = ort.InferenceSession(MODEL, o, providers=["CPUExecutionProvider"])
        self.sr = self.cfg["audio"]["sample_rate"]

    def ids(self, ph):
        m = self.idmap; pad = m["_"][0]
        ids = [m["^"][0], pad]
        for ch in ph:
            if ch in m: ids += [m[ch][0], pad]
        return ids + [m["$"][0]]

    def say(self, text, speaker=0, speed=1.0):
        """Returns float32 mono audio at self.sr. Sentences are synthesised separately with short pauses."""
        parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
        inf = self.cfg["inference"]; chunks = []
        for p in parts:
            ph = phonemize(p)
            x = np.array([self.ids(ph)], dtype=np.int64)
            a = self.sess.run(None, {"input": x, "input_lengths": np.array([x.shape[1]], dtype=np.int64),
                                     "scales": np.array([inf["noise_scale"], inf["length_scale"] / speed, inf["noise_w"]], dtype=np.float32),
                                     "sid": np.array([speaker], dtype=np.int64)})[0].squeeze()
            chunks += [a.astype(np.float32), np.zeros(int(self.sr * .18), np.float32)]
        a = np.concatenate(chunks) if chunks else np.zeros(1, np.float32)
        return a / max(1e-6, np.abs(a).max()) * .9

def write_wav(path, a, sr):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    args = sys.argv[1:]
    sp = int(args[args.index("--speaker") + 1]) if "--speaker" in args else 0
    spd = float(args[args.index("--speed") + 1]) if "--speed" in args else 1.0
    if "--ipa" in args: print(phonemize(args[0])); sys.exit()
    v = Voice(); write_wav(args[1], v.say(args[0], sp, spd), v.sr); print("OK", args[1])
