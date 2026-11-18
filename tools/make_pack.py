#!/usr/bin/env python3
"""Build a song pack for Footnotes from a StepMania pack zip.

From each song it keeps what Footnotes needs: the simfile, the music, and the
banner for the song list. Background videos, backgrounds and other files are left
out. A music or banner file whose name differs only in case from what the simfile
names is saved under the simfile's name, because web servers, unlike Windows, tell
the two apart.

It writes <id>/index.json, which lists the songs and their charts. Charts are
numbered the way Footnotes numbers them in its chartIndex links: by difficulty,
then by level, then in file order. Then it rebuilds packs.json, the list of every
pack in this repository.

Usage, from the repository root:
    python3 tools/make_pack.py <pack.zip> <id> <name> <source page URL>
"""

import hashlib
import json
import os
import posixpath
import re
import shutil
import sys
import zipfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SIMFILE_TYPES = (".ssc", ".sm")
# The order Footnotes sorts charts in, from app/src/chart/sm/ChartTypes.ts
DIFFICULTIES = ["Beginner", "Easy", "Medium", "Hard", "Challenge", "Edit"]


def decode(data):
    for encoding in ("utf-8-sig", "cp932"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode("latin-1")


def strip_comments(text):
    return re.sub(r"//[^\n]*", "", text)


def tags(text):
    """The simfile's #TAG:value; pairs, in order."""
    return [(m.group(1).upper(), m.group(2)) for m in re.finditer(r"#([A-Za-z0-9]+):([^;]*);", text)]


def first(pairs, name):
    return next((value.strip() for key, value in pairs if key == name), "")


def bpm_label(pairs):
    display = first(pairs, "DISPLAYBPM")
    if display:
        if display == "*":
            return "?"
        values = [float(v) for v in display.split(":") if v.strip()]
    else:
        values = []
        for change in first(pairs, "BPMS").split(","):
            if "=" in change:
                values.append(float(change.split("=")[1]))
    values = [v for v in values if v > 0]
    if not values:
        return ""
    low, high = round(min(values)), round(max(values))
    return str(low) if low == high else f"{low}–{high}"


def sm_charts(pairs):
    charts = []
    for key, value in pairs:
        if key != "NOTES":
            continue
        fields = [f.strip() for f in value.split(":")]
        if len(fields) < 6:
            continue
        step_type, description, difficulty, meter = fields[:4]
        charts.append((step_type, difficulty, meter, description))
    return charts


def ssc_charts(text):
    charts = []
    for block in re.split(r"#NOTEDATA:[^;]*;", text)[1:]:
        pairs = tags(block)
        charts.append((
            first(pairs, "STEPSTYPE"),
            first(pairs, "DIFFICULTY"),
            first(pairs, "METER"),
            first(pairs, "DESCRIPTION") or first(pairs, "CREDIT"),
        ))
    return charts


def numbered(charts):
    """Charts as Footnotes lists them: grouped by step type, sorted, numbered."""
    result = []
    usable = [c for c in charts if c[1] in DIFFICULTIES and re.fullmatch(r"\d+", c[2])]
    for step_type in dict.fromkeys(c[0] for c in usable):
        group = [c for c in usable if c[0] == step_type]
        group.sort(key=lambda c: (DIFFICULTIES.index(c[1]), int(c[2])))
        for index, (_, difficulty, meter, description) in enumerate(group):
            result.append({
                "type": step_type,
                "index": index,
                "difficulty": difficulty,
                "meter": int(meter),
                "description": description,
            })
    return result, len(charts) - len(usable)


def find(names, wanted):
    """The file `wanted` names in a song folder: an exact match, else one that differs in case."""
    if not wanted:
        return None
    wanted = posixpath.basename(wanted)
    if wanted in names:
        return wanted
    return next((n for n in names if n.lower() == wanted.lower()), None)


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    zip_path, pack_id, pack_name, source = sys.argv[1:]
    with open(zip_path, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()
    archive = zipfile.ZipFile(zip_path)

    folders = {}
    for name in archive.namelist():
        if not name.endswith("/"):
            folders.setdefault(posixpath.dirname(name), []).append(posixpath.basename(name))

    out = os.path.join(ROOT, pack_id)
    shutil.rmtree(out, ignore_errors=True)
    songs, notes = [], []
    for folder in sorted(folders):
        names = folders[folder]
        simfile = next((n for ext in SIMFILE_TYPES for n in sorted(names) if n.lower().endswith(ext)), None)
        if not simfile:
            continue
        song_id = posixpath.basename(folder)
        if any(s["folder"] == song_id for s in songs):
            notes.append(f"{folder}: skipped, another song folder is also named {song_id}")
            continue
        data = archive.read(f"{folder}/{simfile}")
        text = strip_comments(decode(data))
        pairs = tags(text)
        music = first(pairs, "MUSIC")
        music_file = find(names, music)
        if not music_file:
            notes.append(f"{folder}: skipped, no music file {music!r}")
            continue
        charts, unusable = numbered(ssc_charts(text) if simfile.lower().endswith(".ssc") else sm_charts(pairs))
        if unusable:
            notes.append(f"{folder}: left out {unusable} chart(s) Footnotes can't read")
        if not charts:
            notes.append(f"{folder}: skipped, no charts")
            continue

        song_out = os.path.join(out, song_id)
        os.makedirs(song_out)
        with open(os.path.join(song_out, simfile), "wb") as f:
            f.write(data)
        # Saved under the name the simfile uses, which differs in case from the file's in a few packs
        music_name = posixpath.basename(music)
        if music_file != music_name:
            notes.append(f"{folder}: saved {music_file} as {music_name}, the name the simfile uses")
        with open(os.path.join(song_out, music_name), "wb") as f:
            f.write(archive.read(f"{folder}/{music_file}"))
        banner = first(pairs, "BANNER")
        banner_file = find(names, banner)
        banner_name = None
        if banner_file:
            banner_name = posixpath.basename(banner)
            with open(os.path.join(song_out, banner_name), "wb") as f:
                f.write(archive.read(f"{folder}/{banner_file}"))

        songs.append({
            "folder": song_id,
            "simfile": f"{song_id}/{simfile}",
            "title": first(pairs, "TITLE") or first(pairs, "TITLETRANSLIT") or song_id,
            "subtitle": first(pairs, "SUBTITLE"),
            "artist": first(pairs, "ARTIST") or first(pairs, "ARTISTTRANSLIT"),
            "bpm": bpm_label(pairs),
            "banner": f"{song_id}/{banner_name}" if banner_name else None,
            "charts": charts,
        })

    songs.sort(key=lambda s: (s["title"].lower(), s["subtitle"].lower()))
    index = {
        "id": pack_id,
        "name": pack_name,
        "source": source,
        "archive": {"name": os.path.basename(zip_path), "size": os.path.getsize(zip_path), "sha256": sha256},
        "songs": songs,
    }
    with open(os.path.join(out, "index.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
        f.write("\n")
    write_credits(out, index)
    write_pack_list()

    size = sum(os.path.getsize(os.path.join(d, n)) for d, _, ns in os.walk(out) for n in ns)
    print(f"{pack_name}: {len(songs)} songs, {sum(len(s['charts']) for s in songs)} charts, {size / 1e6:.1f} MB")
    for note in notes:
        print("  ", note)


def write_credits(out, index):
    """<id>/README.md: the songs, their artists and chart descriptions, for GitHub's folder view."""
    lines = [
        f"# {index['name']}",
        "",
        f"From {index['source']} ({index['archive']['name']}, sha256 `{index['archive']['sha256']}`).",
        "Built with `tools/make_pack.py`, which keeps each song's simfile, music and banner.",
        "",
        "| Song | Artist | BPM | Charts | Chart descriptions |",
        "| --- | --- | --- | --- | --- |",
    ]
    for song in index["songs"]:
        title = " ".join(filter(None, [song["title"], song["subtitle"]]))
        charts = ", ".join(
            f"{c['difficulty']} {c['meter']}" + (" (double)" if c["type"] == "dance-double" else "")
            for c in song["charts"]
        )
        authors = ", ".join(dict.fromkeys(c["description"] for c in song["charts"] if c["description"]))
        cells = [title, song["artist"], song["bpm"], charts, authors]
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    with open(os.path.join(out, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def write_pack_list():
    packs = []
    for name in sorted(os.listdir(ROOT)):
        path = os.path.join(ROOT, name, "index.json")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                index = json.load(f)
            packs.append({
                "id": index["id"],
                "name": index["name"],
                "songs": len(index["songs"]),
                "charts": sum(len(s["charts"]) for s in index["songs"]),
                "index": f"{index['id']}/index.json",
                "source": index["source"],
            })
    with open(os.path.join(ROOT, "packs.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"packs": packs}, f, ensure_ascii=False, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
