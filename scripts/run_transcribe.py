#!/usr/bin/env python3
"""Load MOSS-Transcribe-Diarize on a Colab GPU and transcribe one audio file.

Edit the paths below, or pass them as the first lines of a small wrapper.
Defaults match the Drive layout from the first successful run.
"""

import json
import os
import shutil
import sys
import time
import traceback

WEIGHTS = os.environ.get(
    "MOSS_WEIGHTS", "/content/drive/MyDrive/MOSS-Transcribe-Diarize"
)
AUDIO_DIR = os.environ.get(
    "MOSS_AUDIO_DIR",
    "/content/drive/MyDrive/MOSS-Transcribe-Diarize/to-transcribe",
)
AUDIO_SRC = os.environ.get("MOSS_AUDIO", "")
EXPECTED_SF = int(os.environ.get("MOSS_EXPECTED_SF", "1817113576"))
EXPECTED_AUDIO = int(os.environ.get("MOSS_EXPECTED_AUDIO", "0"))
AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".flac", ".aac", ".ogg", ".mp4", ".webm"}
SRC = os.environ.get("MOSS_SRC", "/content/MOSS-Transcribe-Diarize-src")
AUDIO = "/content/moss-input-audio"
OUT = "/content/moss-transcript-raw.txt"
META = "/content/moss-transcript-meta.json"


def log(msg):
    print(msg, flush=True)


def resolve_audio():
    if AUDIO_SRC:
        if not os.path.isfile(AUDIO_SRC):
            raise FileNotFoundError(AUDIO_SRC)
        return AUDIO_SRC
    if not os.path.isdir(AUDIO_DIR):
        raise FileNotFoundError(f"audio folder missing: {AUDIO_DIR}")
    files = sorted(
        p for p in os.listdir(AUDIO_DIR)
        if os.path.splitext(p)[1].lower() in AUDIO_EXTS
        and os.path.isfile(os.path.join(AUDIO_DIR, p))
    )
    log("audio_dir " + AUDIO_DIR)
    log("audio_files " + ", ".join(files))
    if len(files) != 1:
        raise RuntimeError(
            f"{AUDIO_DIR} has {len(files)} audio files; set MOSS_AUDIO to the one to transcribe"
        )
    return os.path.join(AUDIO_DIR, files[0])


def main():
    t0 = time.perf_counter()
    meta = {"ok": False}
    try:
        audio_src = resolve_audio()
        log(f"audio_src {audio_src}")
        sf = os.path.join(WEIGHTS, "model-00000-of-00001.safetensors")
        log(f"drive_mounted {os.path.isdir('/content/drive/MyDrive')}")
        if not os.path.isfile(sf):
            raise FileNotFoundError(sf)
        sf_size = os.path.getsize(sf)
        log(f"sf_size {sf_size}")
        if EXPECTED_SF and sf_size != EXPECTED_SF:
            raise RuntimeError(f"safetensors size {sf_size} != {EXPECTED_SF}")
        audio_size = os.path.getsize(audio_src)
        log(f"audio_size {audio_size}")
        if EXPECTED_AUDIO and audio_size != EXPECTED_AUDIO:
            raise RuntimeError(f"audio size {audio_size} != {EXPECTED_AUDIO}")
        shutil.copy2(audio_src, AUDIO + os.path.splitext(audio_src)[1].lower())
        audio_local = AUDIO + os.path.splitext(audio_src)[1].lower()
        log(f"copied_audio {os.path.getsize(audio_local)}")

        if SRC not in sys.path:
            sys.path.insert(0, SRC)
        from moss_transcribe_diarize.inference_utils import (
            build_transcription_messages,
            generate_transcription,
            prepare_inputs,
            resolve_device,
        )

        import torch
        from transformers import AutoModelForCausalLM, AutoProcessor

        device = resolve_device("auto")
        dtype = torch.bfloat16
        log(f"device {device} dtype {dtype} cuda {torch.cuda.is_available()}")
        if device.type != "cuda":
            raise RuntimeError(f"expected cuda, got {device}")

        t_load = time.perf_counter()
        model = AutoModelForCausalLM.from_pretrained(
            WEIGHTS,
            trust_remote_code=True,
            dtype=dtype,
            attn_implementation="sdpa",
        )
        model = model.to(dtype=dtype).to(device).eval()
        attn = getattr(model.config, "_attn_implementation", None)
        log(f"attn_implementation {attn}")
        if attn != "sdpa":
            raise RuntimeError(f"attn_implementation is {attn}, expected sdpa")
        processor = AutoProcessor.from_pretrained(WEIGHTS, trust_remote_code=True)
        load_s = time.perf_counter() - t_load
        log(f"load_s {load_s:.3f}")

        messages = build_transcription_messages(audio_local)
        t_prep = time.perf_counter()
        inputs = prepare_inputs(processor, messages, max_length=131072, device=device)
        input_length = int(inputs["attention_mask"][0].sum().item())
        prep_s = time.perf_counter() - t_prep
        budget = min(65536, 131072 - input_length - 16)
        log(f"input_length {input_length}")
        log(f"max_new_tokens {budget}")
        log(f"prep_s {prep_s:.3f}")
        del inputs
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        if budget < 1024:
            log("SKIP_GENERATE budget under 1024")
            meta.update(
                ok=False,
                reason="budget_under_1024",
                input_length=input_length,
                max_new_tokens=budget,
            )
            with open(META, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            return

        t_gen = time.perf_counter()
        result = generate_transcription(
            model,
            processor,
            messages,
            max_length=131072,
            max_new_tokens=budget,
            do_sample=False,
            device=device,
            dtype=dtype,
        )
        generate_s = time.perf_counter() - t_gen
        text = result["text"]
        with open(OUT, "w", encoding="utf-8") as f:
            f.write(text)
            if text and not text.endswith("\n"):
                f.write("\n")
        total_s = time.perf_counter() - t0
        log(f"generate_s {generate_s:.3f}")
        log(f"total_s {total_s:.3f}")
        log(f"generated_tokens {result.get('generated_tokens')}")
        log(f"text_chars {len(text)}")
        log(f"out {OUT}")
        meta.update(
            ok=True,
            attn=attn,
            load_s=load_s,
            prep_s=prep_s,
            generate_s=generate_s,
            total_s=total_s,
            input_length=input_length,
            max_new_tokens=budget,
            generated_tokens=result.get("generated_tokens"),
            text_chars=len(text),
            out=OUT,
        )
        with open(META, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        log("RESULT_JSON " + json.dumps(meta, ensure_ascii=False))
        log("DONE")
    except Exception:
        log("FAILED")
        log(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
