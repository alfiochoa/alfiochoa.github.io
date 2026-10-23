#!/usr/bin/env python3
"""Build the web media from the local motion-graphics sources (not stored in this repo; they are ~20 MB each).

  python3 tools/make_media.py [--only slug] [--posters-only]

* videos: the SILENT 1080p motion videos -> 1280x720 H.264 (crf 27, faststart, no audio track); the intro keeps its voice track (AAC 96k)
* posters: one frame per video (JPEG)
* images: screenshots (already cropped for readability) -> WebP
Source folder: $PORTFOLIO_PROFILE (default ~/Documentos/Projects/portfolio-profile).
"""
import os, subprocess, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(os.environ.get("PORTFOLIO_PROFILE", Path.home() / "Documentos/Projects/portfolio-profile"))
MOTION, IMGS = SRC / "videos/motion", SRC / "publish-kit/fiverr-portfolio-images"

# slug -> (motion video, poster time in s, screenshots)
PROJECTS = {
    "n8n-automation-hub": ("gig11-n8n-motion.mp4", 26, ["11-n8n-automation-hub-1", "11-n8n-automation-hub-2", "11-n8n-automation-hub-3"]),
    "ai-business-data-assistant": ("gig1-ai-assistant-motion.mp4", 37, ["01-ai-business-data-assistant-1", "01-ai-business-data-assistant-2"]),
    "payment-reconciliation-pipeline": ("gig3-reconciliation-motion.mp4", 37, ["02-payment-reconciliation-1"]),
    "ai-invoice-intake": ("p3-invoice-intake-motion.mp4", 40, ["03-ai-invoice-intake-1"]),
    "order-ops-automation": ("p4-order-ops-motion.mp4", 28, ["04-order-ops-automation-1"]),
    "price-stock-monitor": ("p5-price-monitor-motion.mp4", 40, ["05-price-stock-monitor-1"]),
    "docs-support-assistant": ("p6-docs-assistant-motion.mp4", 36, ["06-docs-support-assistant-1"]),
    "executive-bi-dashboard": ("p7-bi-dashboard-motion.mp4", 35, ["07-executive-bi-dashboard-1", "07-executive-bi-dashboard-2"]),
    "fx-rate-monitor": ("p8-fx-monitor-motion.mp4", 40, ["08-fx-rate-monitor-1", "08-fx-rate-monitor-2"]),
    "prediction-market-tracker": ("p9-prediction-markets-motion.mp4", 40, ["09-prediction-market-tracker-1"]),
    "sp500-tracker": ("p10-sp500-top200-motion.mp4", 40, ["10-sp500-tracker-1"]),
    "market-desk": ("gig12-market-desk-motion.mp4", 14, ["12-market-desk-1", "12-market-desk-2", "12-market-desk-3"]),
}
EXTRA = {  # name -> (source, poster time, keep audio)
    "showreel": ("showreel-motion.mp4", 3.5, False),
    "intro": ("intro-motion-final.mp4", 2.0, True),
}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stderr[-800:]}")


def video(src, dst, audio):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-vf", "scale=1280:720:flags=lanczos,format=yuv420p",
           "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-r", "30", "-movflags", "+faststart"]
    cmd += ["-c:a", "aac", "-b:a", "96k", "-ac", "1"] if audio else ["-an"]
    run(cmd + [str(dst)])


def poster(src, dst, t):
    tmp = dst.with_suffix(".png")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t), "-i", str(src), "-frames:v", "1", "-vf", "scale=1280:720:flags=lanczos", str(tmp)])
    Image.open(tmp).convert("RGB").save(dst, quality=84, optimize=True, progressive=True); tmp.unlink()


def image(name, slug, n):
    im = Image.open(IMGS / f"{name}.png").convert("RGB")
    im.save(ROOT / f"media/img/{slug}-{n}.webp", quality=82, method=6)


def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    posters_only = "--posters-only" in sys.argv
    for slug, (vid, t, shots) in PROJECTS.items():
        if only and only != slug: continue
        src = MOTION / vid
        poster(src, ROOT / f"media/poster/{slug}.jpg", t)
        if not posters_only:
            video(src, ROOT / f"media/video/{slug}.mp4", False)
            for n, s in enumerate(shots, 1): image(s, slug, n)
        print("ok", slug, flush=True)
    for name, (vid, t, audio) in EXTRA.items():
        if only and only != name: continue
        src = MOTION / vid
        poster(src, ROOT / f"media/poster/{name}.jpg", t)
        if not posters_only: video(src, ROOT / f"media/video/{name}.mp4", audio)
        print("ok", name, flush=True)


if __name__ == "__main__":
    main()
