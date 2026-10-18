"""Render the release video: python render_release_video.py [release-template.html] [out.mp4]
Needs: playwright (chromium) + ffmpeg. The HTML exposes setT(t) and D (duration in s)."""
import asyncio, os, subprocess, sys, tempfile
from playwright.async_api import async_playwright
src = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "release-template.html")
out = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else "release.mp4")
tmp = tempfile.mkdtemp()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1280, "height": 720})
        await pg.goto("file://" + src + "#manual")
        n = int(await pg.evaluate("D") * 20)
        for i in range(n):
            await pg.evaluate(f"setT({i/20})")
            await pg.screenshot(path=f"{tmp}/{i:04d}.jpg", type="jpeg", quality=88)
        await b.close()
asyncio.run(main())
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "20", "-i", f"{tmp}/%04d.jpg", "-c:v", "libx264",
                "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "20", "-r", "30", "-movflags", "+faststart", out], check=True)
print("ok", out)
