# When a step fails

## Model

- Code: https://github.com/OpenMOSS/MOSS-Transcribe-Diarize
- Weights: https://huggingface.co/OpenMOSS-Team/MOSS-Transcribe-Diarize
- Drive weights: `/content/drive/MyDrive/MOSS-Transcribe-Diarize` (https://drive.google.com/drive/folders/1dWi-iifer8XVDEilmjjUyI-dfNO5crZk)
- Drop folder: `/content/drive/MyDrive/MOSS-Transcribe-Diarize/to-transcribe` (https://drive.google.com/drive/folders/1isoq9Acb1DAv42nEhXZ_QeV9hMkSzCIH)
- Markdown output: `/content/drive/MyDrive/MOSS-Transcribe-Diarize/transcripts` (https://drive.google.com/drive/folders/1xBYHfh-k3uKFMGof4gCN0UkfjNdhk2Ix)
- That Markdown is the checklist. Same stem as the audio means done. Missing Markdown means still to do.
- Use `build_transcription_messages` and `generate_transcription`.
- Attention stays `sdpa`. If the loaded config says anything else, stop.
- Context is 131072. A single pass stops when that fills. Treat about 90 minutes as the hard stop. Do not generate when fewer than 1024 new tokens remain.
- Raw output looks like `[0.15][S01]text[2.48]`. Hand over the Markdown, and keep the raw string.

## Colab

- `colab new` rents a VM. It does not create a notebook.
- `colab exec -f` runs the local script on the remote kernel. Kernel state survives until `stop`.
- Working directory on the VM is `/content`.
- `drivemount` opens `/dev/tty` and fails without a terminal. A person has to approve Drive.
- `drive.file` on the CLI token cannot read files the user uploaded. The mount is what makes the weights visible.
- After `stop`, `sessions` should show no active assignment and `usage` should show `0.00/hr`.

## Markdown

`scripts/format_transcript.py` groups consecutive same-speaker utterances when the gap is under 1.5 seconds. Each utterance stays on its own line. Timestamps are `mm:ss`, or `h:mm:ss` past one hour.
