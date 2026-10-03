# moss-transcribe-diarize

Agent skill for turning one spoken clip into a speaker-labeled Markdown transcript with MOSS-Transcribe-Diarize on a Colab L4, then stopping the VM.

Drop the audio in the Drive folder named in `SKILL.md`. The skill keeps the raw model string and writes Markdown with `scripts/format_transcript.py`. Speaker names are only added when you pass them; they are not guessed from the audio.

Install by copying this folder into your agent's skills directory. It is written for Pi, Antigravity CLI, and Grok Bot.
