#!/usr/bin/env python3

# Copyright (c) 2026, PawAI contributors
# SPDX-License-Identifier: BSD-3-Clause

import argparse

import numpy as np
import sounddevice as sd


def list_input_devices() -> None:
    print("Input devices:")
    for i, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0:
            print(f"  {i}: {dev['name']} (default_sr={dev['default_samplerate']})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Quick microphone RMS/VAD check")
    parser.add_argument("--seconds", type=float, default=2.0, help="record duration")
    parser.add_argument("--sample-rate", type=int, default=16000, help="capture sample rate")
    parser.add_argument("--channels", type=int, default=1, help="record channels")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.015,
        help="energy VAD start threshold for comparison",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="input device index (default: sounddevice default input)",
    )
    args = parser.parse_args()

    default_device = sd.default.device
    print(f"default device tuple: {default_device}")
    try:
        default_input = sd.query_devices(kind="input")
        print(f"default input: {default_input['name']} (sr={default_input['default_samplerate']})")
    except Exception as exc:
        print(f"default input query failed: {exc}")

    list_input_devices()

    frames = int(args.seconds * args.sample_rate)
    print(
        f"\nrecording {args.seconds:.2f}s, rate={args.sample_rate}, "
        f"channels={args.channels}, device={args.device}"
    )
    rec = sd.rec(
        frames,
        samplerate=args.sample_rate,
        channels=args.channels,
        dtype="float32",
        device=args.device,
    )
    sd.wait()

    rms = float(np.sqrt(np.mean(rec**2)))
    peak = float(np.max(np.abs(rec)))
    print(f"RMS: {rms:.6f}")
    print(f"Peak: {peak:.6f}")
    print(f"trigger@{args.threshold:.3f}: {rms > args.threshold}")


if __name__ == "__main__":
    main()
