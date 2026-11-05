#!/usr/bin/env bash
# Fetch the offline English voice (Piper en_US-libritts_r-medium, MIT model; LibriTTS-R data CC BY 4.0)
# and the CMU pronouncing dictionary into tools/voice/models/ (git-ignored).
# pip / HuggingFace are blocked in the cloud sandbox, so both come from public GitHub repos via git.
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)/models"
mkdir -p "$D"; cd "$D"
if [ ! -s en_US-libritts_r-medium.onnx ]; then
  rm -rf _piper && git clone -q --depth 1 --filter=blob:none --no-checkout https://github.com/clowerweb/tts-studio _piper
  (cd _piper && git checkout HEAD -- public/tts-models/piper/en_US-libritts_r-medium.onnx public/tts-models/piper/en_US-libritts_r-medium.onnx.json)
  mv _piper/public/tts-models/piper/en_US-libritts_r-medium.onnx* . && rm -rf _piper
fi
echo "10bb85e071d616fcf4071f369f1799d0491492ab3c5d552ec19fb548fac13195  en_US-libritts_r-medium.onnx" | sha256sum -c -
if [ ! -s cmudict.dict ]; then
  rm -rf _cmu && git clone -q --depth 1 https://github.com/cmusphinx/cmudict _cmu && mv _cmu/cmudict.dict . && rm -rf _cmu
fi
ls -la "$D"
