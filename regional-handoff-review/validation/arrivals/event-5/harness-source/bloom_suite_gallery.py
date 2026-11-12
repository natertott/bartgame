"""Publish existing real-mGBA Bloom captures without rerendering game art.

python tools/bloom_suite_gallery.py BEFORE AFTER OUT

Copies only the five canonical capture groups. Full-frame before/after GIFs
are synchronized using their recorded GIF durations; headers are the only new
pixels. Native PNGs remain byte-for-byte copies. The optional MP4 is a lossy
30-fps review convenience, with the original GIF/PNG evidence retained.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

GROUPS = ("drain", "worlds", "special-v2", "fore", "interrupt")
PAIRS = (
    ("north-shield-wood", "drain", "drain-shield-wood-n"),
    ("north-shield-green", "drain", "drain-shield-green-n"),
    ("north-sword", "drain", "drain-sword-n"),
    ("north-bow", "drain", "drain-bow-n"),
    ("north-lamp", "drain", "drain-lamp-n"),
    ("lift-carry-throw", "special-v2", "lift-carry-throw-bush-n"),
    ("cape-jump", "worlds", "blight-cape-e"),
    ("drowning", "special-v2", "forest-drowning"),
    ("death", "special-v2", "forest-death"),
    ("air-hurt-recovery", "interrupt", "air-hurt-recovery"),
    ("roll-wall-bounce", "interrupt", "roll-wall-bounce"),
    ("shield-walk", "drain", "drain-shield-walk-n"),
    ("roll", "drain", "drain-roll-n"),
    ("pit-fall", "special-v2", "forest-pit-fall"),
    ("cap-return-drop-in", "special-v2", "forest-cap-return-drop-in"),
)
FONT = ImageFont.load_default()
HEADER = 22
BG = (12, 17, 25)
FG = (243, 227, 174)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_gif(path):
    frames = []
    durations = []
    with Image.open(path) as gif:
        for tick in range(gif.n_frames):
            gif.seek(tick)
            frames.append(gif.convert("RGB").copy())
            durations.append(gif.info.get("duration", 30))
    return frames, durations


def label(image, text):
    out = Image.new("RGB", (image.width, image.height + HEADER), BG)
    out.paste(image, (0, HEADER))
    ImageDraw.Draw(out).text((8, 5), text, fill=FG, font=FONT)
    return out


def write_gif(frames, durations, path):
    colors = set()
    for frame in frames:
        colors.update(color for _, color in frame.getcolors(frame.width * frame.height))
    exact = len(colors) <= 256
    if exact:
        palette = Image.new("P", (1, 1))
        raw = [channel for color in sorted(colors) for channel in color]
        palette.putpalette(raw + [0] * (768 - len(raw)))
        converted = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    else:
        converted = [frame.quantize(colors=256, dither=Image.Dither.NONE) for frame in frames]
    converted[0].save(path, save_all=True, append_images=converted[1:],
                      duration=durations, loop=0, disposal=2, optimize=False)
    return {"exact_palette": exact, "colour_count": len(colors),
            "duration_ms": sum(durations), "timeline_frames": len(frames)}


def compare(before, after, path, name):
    left, ld = load_gif(before)
    right, rd = load_gif(after)
    assert sum(ld) == sum(rd), (name, sum(ld), sum(rd))
    boundaries = {0}
    for durations in (ld, rd):
        t = 0
        for duration in durations:
            t += duration
            boundaries.add(t)
    boundaries = sorted(boundaries)
    ends = []
    for durations in (ld, rd):
        total = 0
        row = []
        for duration in durations:
            total += duration
            row.append(total)
        ends.append(row)
    frames = []
    durations = []
    li = ri = 0
    for start, end in zip(boundaries, boundaries[1:]):
        while start >= ends[0][li]:
            li += 1
        while start >= ends[1][ri]:
            ri += 1
        a = label(left[li], "BEFORE | " + name)
        b = label(right[ri], "AFTER | " + name)
        out = Image.new("RGB", (a.width + b.width, a.height), BG)
        out.paste(a, (0, 0)); out.paste(b, (a.width, 0))
        frames.append(out); durations.append(end - start)
    info = write_gif(frames, durations, path)
    # The contact is for rapid visual inspection; the GIF preserves timing.
    picks = [min(len(frames)-1, int((len(frames)-1)*p)) for p in (0.15, 0.4, 0.65, 0.9)]
    contact = Image.new("RGB", (frames[0].width, frames[0].height*4), BG)
    for row, index in enumerate(picks):
        contact.paste(frames[index], (0, row*frames[0].height))
    contact.save(path.with_name(path.stem + "-contact.png"))
    return info


def make_video(root, output):
    clips = []
    for background in ("drain", "forest", "blight", "cave"):
        group = "drain" if background == "drain" else "worlds"
        for action in ("sword-n", "shield-wood-n", "cape-e", "bow-n", "lamp-n"):
            clips.append((group, background + "-" + action))
    clips.extend((group, name) for _, group, name in PAIRS if group in ("special-v2", "interrupt"))
    command = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", "480x342", "-r", "30", "-i", "-", "-an", "-c:v", "libx264",
               "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE)
    count = 0
    try:
        for group, name in clips:
            frames, durations = load_gif(root/group/(name+".gif"))
            total = sum(durations)
            for repeat in range(2):
                pos = end = 0
                for tick in range(round(total*30/1000)):
                    target = tick*1000/30
                    while pos < len(frames)-1 and target >= end+durations[pos]:
                        end += durations[pos]; pos += 1
                    proc.stdin.write(label(frames[pos], "mGBA FINAL | " + name).tobytes())
                    count += 1
        proc.stdin.close()
        if proc.wait():
            raise RuntimeError("ffmpeg did not finish successfully")
    except BaseException:
        proc.kill()
        proc.wait()
        raise
    return {"path": output.name, "frames": count, "fps": 30,
            "seconds": count/30, "clips": [name for _, name in clips],
            "note": "Lossy H.264 review reel; GIFs and native PNGs are the primary capture evidence."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--no-video", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    indexes = {}
    counts = {}
    for label_name, source in (("before", args.before), ("after", args.after)):
        index = json.loads((source/"suite-index.json").read_text())
        assert index["count"] == 99
        indexes[label_name] = index
        shutil.copyfile(source/"suite-index.json", args.out/("suite-index-"+label_name+".json"))
        copied = 0
        matching_gameplay = 0
        for group in GROUPS:
            destination = args.out/label_name/group
            destination.mkdir(parents=True, exist_ok=True)
            report = json.loads((source/group/"suite.json").read_text())
            assert report["rom_sha256"] == index["rom_sha256"]
            shutil.copyfile(source/group/"suite.json", destination/"suite.json")
            assert not report["missing"], (label_name, group, report["missing"])
            for capture in report["captures"]:
                if label_name == "after":
                    comparison = capture["gameplay_comparison"]
                    assert comparison["matched_fixture"], capture["name"]
                    matching_gameplay += not comparison["different_frames"]
                name = capture["name"]
                files = [name+".gif", capture["filmstrip"], *capture["native_frames"]]
                for relative in files:
                    src, dst = source/group/relative, destination/relative
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, dst)
                copied += 1
        assert copied == 99
        if label_name == "after":
            assert matching_gameplay == 97
        counts[label_name] = {"captures": copied,
                              "exact_palette_gifs": sum(c["gif"]["exact_palette"] for group in GROUPS
                                  for c in json.loads((source/group/"suite.json").read_text())["captures"])}
    comparisons = args.out/"comparisons"
    comparisons.mkdir(exist_ok=True)
    rows = []
    for short, group, name in PAIRS:
        path = comparisons/(short+".gif")
        info = compare(args.out/"before"/group/(name+".gif"),
                       args.out/"after"/group/(name+".gif"), path, name)
        rows.append({"name": short, "capture": name, "group": group,
                     "gif": str(path.relative_to(args.out)), **info})
        print("comparison", short, flush=True)
    manifest = {"method": "Existing real mGBA framebuffers copied byte-for-byte; comparison images add headers and juxtapose synchronized whole frames.",
                "before_rom_sha256": indexes["before"]["rom_sha256"],
                "after_rom_sha256": indexes["after"]["rom_sha256"],
                "counts": counts, "comparisons": rows,
                "ordinary_captures_with_identical_gameplay_traces": 97,
                "intentional_recovery_fixes": ["air-hurt-recovery", "roll-wall-bounce"],
                "gif_note": "GIFs sample every two native video frames. Two transition clips exceed GIF's 256-color union; their original native PNGs retain exact colors."}
    assert {c["name"] for c in indexes["after"]["gameplay_differences"]} == set(manifest["intentional_recovery_fixes"])
    if not args.no_video:
        manifest["video"] = make_video(args.out/"after", args.out/"bloom-suite-reel.mp4")
    manifest["files"] = [{"path": str(path.relative_to(args.out)), "bytes": path.stat().st_size,
                          "sha256": digest(path)} for path in sorted(args.out.rglob("*"))
                         if path.is_file() and (path.relative_to(args.out).parts[0] in ("before", "after", "comparisons")
                            or path.name in ("suite-index-before.json", "suite-index-after.json", "bloom-suite-reel.mp4"))]
    (args.out/"gallery-manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps({"counts": counts, "files": len(manifest["files"]),
                      "bytes": sum(f["bytes"] for f in manifest["files"]),
                      "video": manifest.get("video")}, indent=2))


if __name__ == "__main__":
    main()
