from __future__ import annotations

import argparse

from servicebridge.local_runtime.tts import generate_kokoro_local


def main():
    parser = argparse.ArgumentParser(
        description="Generate speech with Kokoro using already-cached local weights/voices."
    )
    parser.add_argument("--text", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--voice", default="af_heart")
    parser.add_argument("--lang", default="a")
    parser.add_argument("--speed", type=float, default=1.0)
    args = parser.parse_args()

    result = generate_kokoro_local(
        args.text,
        output_wav=args.output,
        voice=args.voice,
        lang_code=args.lang,
        speed=args.speed,
    )
    print(result)


if __name__ == "__main__":
    main()
