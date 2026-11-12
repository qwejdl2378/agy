# Visual similarity of two screenshots (0..1): downscale to 120x76, blur-ish, compare per-channel.
# usage: uv run --with pillow --with numpy python imgsim.py a.png b.png
import sys
import numpy as np
from PIL import Image, ImageFilter
def load(p):
    im = Image.open(p).convert("RGB").resize((1200, 760)).filter(ImageFilter.GaussianBlur(3)).resize((240, 152))
    return np.asarray(im, dtype=np.float32) / 255
a, b = load(sys.argv[1]), load(sys.argv[2])
print(round(float(1 - np.abs(a - b).mean() * 4), 4))  # x4: a 25% mean channel error scores 0
