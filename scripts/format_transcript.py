#!/usr/bin/env python3
"""Turn a MOSS-Transcribe-Diarize raw string into readable Markdown."""

import argparse
import re
from pathlib import Path


PAT = re.compile(r"\[(\d+\.\d+)\]\[(S\d+)\](.*?)\[(\d+\.\d+)\]")


def clock(seconds: str) -> str:
    total = int(float(seconds))
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def parse(text: str):
    segs = []
    for start, speaker, utterance, end in PAT.findall(text.strip()):
        utterance = re.sub(r"\s+", " ", utterance).strip()
        if utterance:
            segs.append((start, speaker, utterance, end))
    if not segs:
        raise SystemExit("no [time][Sxx]utterance[time] segments found")
    return segs


def blocks(segs, gap: float):
    i = 0
    while i < len(segs):
        j = i + 1
        while (
            j < len(segs)
            and segs[j][1] == segs[i][1]
            and float(segs[j][0]) - float(segs[j - 1][3]) < gap
        ):
            j += 1
        yield segs[i:j]
        i = j


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    parser.add_argument("markdown")
    parser.add_argument("--title", default="Transcript")
    parser.add_argument("--source", default="")
    parser.add_argument("--duration", default="")
    parser.add_argument("--note", default="")
    parser.add_argument("--gap", type=float, default=1.5)
    parser.add_argument(
        "--speaker",
        action="append",
        default=[],
        help="Map a model id, e.g. S01=Host. Repeat for each speaker.",
    )
    args = parser.parse_args()
    names = {}
    for item in args.speaker:
        key, _, value = item.partition("=")
        if not value:
            raise SystemExit(f"--speaker must look like S01=Name, got {item}")
        names[key] = f"{key} · {value}"

    segs = parse(Path(args.raw).read_text(encoding="utf-8"))
    lines = [f"# {args.title}", ""]
    meta = []
    if args.source:
        meta.append(f"Source: {args.source}")
    if args.duration:
        meta.append(f"Duration: {args.duration}")
    if meta:
        lines.append(" ".join(meta))
        lines.append("")
    note = args.note or (
        "Speaker ids come from the model. Names appear only when passed with --speaker."
    )
    lines.extend([note, ""])
    for group in blocks(segs, args.gap):
        start, speaker, _, _ = group[0]
        end = group[-1][3]
        label = names.get(speaker, speaker)
        lines.append(f"**{label}** {clock(start)}–{clock(end)}")
        lines.append("")
        for _, _, utterance, _ in group:
            lines.append(utterance)
            lines.append("")
    Path(args.markdown).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {args.markdown} segments={len(segs)}")


if __name__ == "__main__":
    main()
