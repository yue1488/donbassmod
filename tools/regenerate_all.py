"""Regenerate every generated file from tools/content.py and validate the result.
Run from anywhere:  python tools/regenerate_all.py
Needs: Pillow + numpy (textures, sounds) and ffmpeg with libvorbis (sound encoding)."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# gen_textures.py also runs gen_textures_gear.py (armour layers, gear icons, NPC skins)
# gen_sounds.py must run before gen_resources.py: the latter merges the sound subtitles into the lang files
for script in ("gen_textures.py", "gen_sounds.py", "gen_resources.py", "gen_worldgen.py", "gen_structures.py",
               "validate.py"):
    print(f"== {script}")
    result = subprocess.run([sys.executable, os.path.join(HERE, script)], cwd=HERE)
    if result.returncode:
        sys.exit(result.returncode)
