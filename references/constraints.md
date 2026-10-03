# Constraints that already bit this workflow

## Model

- Repo: https://github.com/OpenMOSS/MOSS-Transcribe-Diarize
- Weights: https://huggingface.co/OpenMOSS-Team/MOSS-Transcribe-Diarize
- Local snapshot, if present: `/workspace/models/MOSS-Transcribe-Diarize`. Do not delete it.
- Use the official helpers `build_transcription_messages` and `generate_transcription` when the installed package provides them.
- Attention must stay `sdpa`. If the loaded config reports anything else, stop. Do not fall back to eager and do not edit the model source.
- Context is 131072. A single pass stops when that fills, not when 24 GB runs out. The first run treated roughly 90 minutes of audio as the hard stop. A short clip that leaves fewer than 1024 new tokens must not be generated.
- The raw string looks like `[0.15][S01]text[2.48][2.51][S02]text[2.83]`. That is the model output, not the file to hand over.

## This account's files

These paths are from the first run. Another machine may not have them.

- Weights directory on Drive: `/content/drive/MyDrive/MOSS-Transcribe-Diarize`
- Drive folder: https://drive.google.com/drive/folders/1dWi-iifer8XVDEilmjjUyI-dfNO5crZk
- Short clip used: https://www.youtube.com/watch?v=JlDyHEgd_cI
  Title: 【节目采访】锐波科技创始人孙宇晨做客《鲁豫有约》
  Duration 697.9 s, m4a, 11287566 bytes.
- Audio on Drive: folder `1R6Ra_EhUvzwxYUuloNMpknBbXEBqWKTC`
- Drop folder for new audio: `/content/drive/MyDrive/MOSS-Transcribe-Diarize/to-transcribe`. Put files here. The finished Markdown goes back into the same folder, named after the audio file.
  Drive folder: https://drive.google.com/drive/folders/1isoq9Acb1DAv42nEhXZ_QeV9hMkSzCIH (id `1isoq9Acb1DAv42nEhXZ_QeV9hMkSzCIH`).
- Do not transcribe `/workspace/moss-audio-zh/audio.m4a` (the 66-minute file) or the English Cardi B audio under `/workspace/moss-audio/`.

## Colab CLI

- `colab new` rents a VM. It does not create a Drive notebook.
- `colab exec -f` reads the local script and runs it on the remote kernel. Kernel state survives later execs until `stop` or `restart-kernel`.
- Working directory on the VM is `/content`.
- `drivemount` opens `/dev/tty` and fails with `ENXIO` when there is no terminal. A human has to approve the Drive consent page.
- After `stop`, `status -s moss-zh` should say the session is not found, and `sessions` should show no active assignment.
- `usage` prints `Current balance` and `Usage rate`. Rate should be `0.00/hr` after the stop.

## Audio

- If YouTube only offers a combined format, download that and copy the audio with `ffmpeg -vn -c:a copy`. Do not re-encode unless copy fails.
- Record duration with ffprobe and put it in the Markdown header.
- Check the file size on the VM before load. Refuse to run if it does not match the file you meant to transcribe.

## Markdown

`scripts/format_transcript.py` groups consecutive same-speaker utterances when the gap is under 1.5 seconds. Each original utterance stays on its own line so clauses are not glued into one sentence. Timestamps are `mm:ss`.

Pass `--speaker S01=Name` only for speakers you can actually identify.
