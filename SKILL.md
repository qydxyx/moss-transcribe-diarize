---
name: moss-transcribe-diarize
description: >-
  Transcribe the next unfinished audio or video file with
  MOSS-Transcribe-Diarize on a Colab L4 and write a speaker-labeled Markdown
  transcript. Use when the user asks to transcribe an interview, podcast, or
  other spoken recording with speaker labels, including a long recording or the
  remaining files in the drop folder, or names this workflow. Do not use it for
  a generic speech-to-text API or for editing an existing transcript.
---
# MOSS-Transcribe-Diarize

Transcribe the next unfinished file in the Drive drop folder on a Colab L4, write Markdown, then stop the VM.

## Done when

- The Markdown covers the whole file. Each block is one speaker, with a clock range, and each model utterance on its own line.
- The header names the source file or URL.
- The session is stopped. Report duration, load time, generate time, total time, and compute units spent.
- The Drive weights are still there.

## Audio

New files go in `/content/drive/MyDrive/MOSS-Transcribe-Diarize/to-transcribe`. Transcribe only a file in that folder. One file per VM run.

Before renting a VM, list the audio there and the Markdown already in `/content/drive/MyDrive/MOSS-Transcribe-Diarize/transcripts`. A file is done when `transcripts` has `<same-name>.md`. Skip those. The Markdown is the checklist, so do not add a second list.

If they name a file that is not done, use that. Otherwise take the unfinished files in name order, one this run, and say which names are still waiting. If every file already has a Markdown, stop and say so. Do not transcribe a file again unless they explicitly ask to redo it.

Weights stay in `/content/drive/MyDrive/MOSS-Transcribe-Diarize`. Load from that path. If the safetensors file is already there, do not re-download it and do not copy it off Drive.

## Run

Binary, if present: `/workspace/colab-cli/bin/colab`. If `~/.config/colab-cli/token.json` exists, pass `--auth=oauth2`.

```bash
colab --auth=oauth2 usage
colab --auth=oauth2 new -s moss --gpu L4
```

A 400 means no L4 quota. Stop. Do not use A100, T4, or CPU. Pass `L4` exactly.

Note the balance before you start. An idle L4 still bills.

`colab exec` streams stdout in the terminal that launched it. Do not open a browser to watch. `colab drivemount` needs a real terminal; if Drive is not mounted, say so. Do not run `repl`, `console`, or `auth` without a TTY.

Set `MOSS_AUDIO` inside `scripts/run_transcribe.py` to the one unfinished file this run. A local shell export does not reach the VM.

```bash
colab --auth=oauth2 exec -s moss -f scripts/run_transcribe.py --timeout 7200
```

The script loads with `attn_implementation="sdpa"` and bfloat16. `max_new_tokens` is the context left after the audio: `131072 - input_length - 16`. If that is under 1024, it does not generate. Tell the user the file does not fit one pass. Do not split it, switch models, or use eager attention.

Keep the stdout. It prints `load_s`, `generate_s`, `total_s`, and `DONE` or `FAILED`.

Download `/content/moss-transcript-raw.txt` as the raw model string. Then:

```bash
python3 scripts/format_transcript.py raw.txt transcript.md \
  --title "Title" \
  --source "url or filename"
```

Pass `--speaker S01=Name` only when the user or the recording identifies that speaker. Say the model did not recognize the name.

Put the Markdown in `/content/drive/MyDrive/MOSS-Transcribe-Diarize/transcripts`, named after the audio. Put the raw txt in that same folder.

## Stop

```bash
colab --auth=oauth2 stop -s moss
colab --auth=oauth2 sessions
colab --auth=oauth2 usage
```

Confirm the session is gone and the usage rate is 0. Report duration, the three timings, how long the VM was rented, and balance before minus balance after.

One pass, not playback. Read [references/constraints.md](references/constraints.md) only if a step fails.
