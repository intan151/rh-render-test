#!/usr/bin/env python3
"""Tes render 10 detik pertama Hari 31 (pipeline RH stickman ASLI) di mesin cloud.
Mengimpor render_rh31 (SPEC + frame() yang sama dengan produksi), render 240
frame -> ffmpeg -> test-hari31-10s.mp4. Kalau ini jalan, video penuh juga jalan.
"""
import os, subprocess, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import render_rh31 as R  # top-level: load segments/scene_map, print bounds

TEST_S = 10
N = R.FPS * TEST_S
OUT = os.path.join(BASE, "test-hari31-10s.mp4")
dip_a, dip_b = min(R.bounds[6], TEST_S), min(R.bounds[7], TEST_S)
cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{R.W}x{R.H}",
       "-r", str(R.FPS), "-i", "-", "-i", R.NAR, "-stream_loop", "-1", "-i", R.MUS,
       "-filter_complex",
       f"[1:a]adelay=700|700,apad[a0];"
       f"[2:a]atrim=0:{TEST_S},volume='0.06*if(between(t,{dip_a:.1f},{dip_b:.1f}),0.5,1)':eval=frame,"
       f"afade=t=out:st={TEST_S-2}:d=2[mus];"
       "[a0][mus]amix=inputs=2:duration=first:normalize=0[aout]",
       "-map", "0:v", "-map", "[aout]", "-t", str(TEST_S),
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
       "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", OUT]
t0 = time.time()
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for i in range(N):
    img = R.frame(i / R.FPS)
    try:
        p.stdin.write(img.tobytes())
    except BrokenPipeError:
        break
    if i % 120 == 0:
        print(f"frame {i}/{N} t={i/R.FPS:.1f}s elapsed={time.time()-t0:.1f}s", flush=True)
p.stdin.close()
p.wait()
el = time.time() - t0
print("ffmpeg rc", p.returncode, "total", round(el, 1), "s")
print("SPEED:", round(N / max(el, 0.01), 1), "frame/detik")
if p.returncode == 0 and os.path.exists(OUT):
    print("OUT:", OUT, os.path.getsize(OUT), "bytes")
    subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                    "format=duration,size", "-show_entries", "stream=width,height,codec_name",
                    "-of", "default=noprint_wrappers=1", OUT])
else:
    sys.exit(1)
