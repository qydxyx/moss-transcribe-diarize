---
name: moss-transcribe-diarize
description: >-
  Transcribe a spoken clip with MOSS-Transcribe-Diarize on a Colab L4 and write
  a speaker-labeled Markdown transcript. Use when the user asks to transcribe an
  interview, podcast, or YouTube clip with speaker labels, mentions
  MOSS-Transcribe-Diarize, or wants this Colab diarization workflow repeated. Do
  not use it for a generic speech-to-text API or for editing an existing
  transcript.
---
# MOSS-Transcribe-Diarize

Turn one audio or video clip into a full speaker-labeled Markdown transcript on a rented Colab L4, then release the VM.

## What good looks like

- One Markdown file covering the whole clip, not a sample.
- Each block is one speaker, with a clock range, and each model utterance on its own line.
- The header names the source URL or file.
- The session is stopped. Report load time, generate time, total time, and compute units spent.
- Local weights and Drive files are left in place.

## Before spending compute

1. Use the file or URL the user gave. Search for a public clip only if they asked you to find one, and put that exact URL in the header.
2. Audio to transcribe lives in one Drive folder: `/content/drive/MyDrive/MOSS-Transcribe-Diarize/to-transcribe`. If they name a file, use that file in this folder. If they do not name one and the folder has exactly one audio file, use it. If it has several, list the names and transcribe only the ones they asked for, one file per VM run. Do not pick up files outside this folder, including the old 66-minute interview or the English clip.
3. Prefer a clip that already fit this model: about 12 minutes used 9207 input tokens. Check `input_length` before generating. If `max_new_tokens` would be under 1024, stop and say so. Do not split, summarize, or switch models to force it through.
4. Confirm the L4 weights file is the expected size before loading. On the setup from the first run, `model-00000-of-00001.safetensors` is 1817113576 bytes at `/content/drive/MyDrive/MOSS-Transcribe-Diarize`. Load from the mounted Drive path. Do not copy the 1.8 GB file off Drive, and do not re-download it from Hugging Face if that file is already there.
5. Read `colab usage` and remember the balance. An idle L4 still bills, so do not leave the session up after the file is saved.

## Colab

Binary, if this machine already has the surviving install: `/workspace/colab-cli/bin/colab`. Otherwise `uv tool install google-colab-cli` or `pip install google-colab-cli`.

If `~/.config/colab-cli/token.json` exists, pass `--auth=oauth2` and do not open a browser unless a call returns 401 or 403.

```bash
colab --auth=oauth2 usage
colab --auth=oauth2 new -s moss-zh --gpu L4
```

A 400 on `colab new --gpu L4` means this account has no L4 quota. Stop and say so. Do not retry on A100, T4, or CPU. An unrecognized GPU name can silently fall back to A100, so pass `L4` exactly.

`colab exec` and `colab run` already stream kernel stdout in the terminal that launched them. There is no `--follow`. `colab log` is only a snapshot. Do not open a browser to watch.

`colab drivemount` needs a real terminal. Do not run it from a non-interactive agent shell. If Drive is not mounted, the kernel's `drive.mount` times out in about two minutes and still needs the user to approve access. `drive.file` on the CLI token cannot read files the user uploaded; the mount is what makes the weights visible.

Do not run `repl`, `console`, or `auth` without a TTY.

## Run

Copy `scripts/run_transcribe.py`. It loads weights from the Drive folder above and audio from `to-transcribe`. Set `MOSS_AUDIO` in the script to a file in that folder when more than one is waiting. `colab exec` runs on the VM, so a local shell export does not change those paths. It loads with `attn_implementation="sdpa"` and bfloat16, and sets:

```text
max_new_tokens = min(65536, 131072 - input_length - 16)
```

Do not leave the Hugging Face default of 5120. Do not use eager attention, and do not install flash-attn. `do_sample` stays false.

```bash
colab --auth=oauth2 exec -s moss-zh -f scripts/run_transcribe.py --timeout 7200
```

Run that in the terminal you can watch, and keep its stdout. The script prints `load_s`, `generate_s`, `total_s`, and `DONE` or `FAILED`.

Download `/content/moss-transcript-raw.txt` only as the raw model string. The deliverable is Markdown:

```bash
python3 scripts/format_transcript.py raw.txt transcript.md \
  --title "Program title" \
  --source "https://..."
```

Map `S01` to a real name only when the recording or the user identifies that speaker. Say the names were assigned from the program, not recognized by the model.

Upload the Markdown into `to-transcribe`, named after the audio file, if a Drive upload tool exists. Keep the raw txt. Do not delete weights.

## Stop and report

```bash
colab --auth=oauth2 stop -s moss-zh
colab --auth=oauth2 sessions
colab --auth=oauth2 usage
```

Confirm the session is gone. Report:

- audio duration
- load, generate, and total seconds from the script
- how long the VM was rented, because setup and idle time bill too
- compute units: balance before minus balance after
- local path and Drive link

The first successful run, for calibration: an 11:38 clip, input length 9207, load 35 s, generate 303 s, script total 355 s. The L4 was rented about 31 minutes including Drive setup and cost 0.75 compute units. Generation is one pass, so there is no "minute 4 of 11" progress line while it runs.

## More detail

Read [references/constraints.md](references/constraints.md) if a step fails or the clip is not the short interview from the first run.
