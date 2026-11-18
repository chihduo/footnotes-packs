# Footnotes song packs

Song packs for [Footnotes](https://chihduo.github.io/footnotes/), a tool for learning to dance StepMania charts.
GitHub Pages serves this repository at https://chihduo.github.io/footnotes-packs/, and the [Songs page](https://chihduo.github.io/footnotes/songs/) in Footnotes opens the songs from there.

## Packs

| Pack | Songs | Charts | Source |
| --- | --- | --- | --- |
| [Mintmania](mintmania/) | 52 | 257 | [stepmaniaonline.net/pack/2636](https://stepmaniaonline.net/pack/2636) |

Each pack's folder has an `index.json` that lists its songs and charts, and a README with the songs, their artists and their chart descriptions.

## What's in a pack

Each song keeps only what Footnotes needs: its simfile, its music, and its banner for the song list.
Background videos, backgrounds and other files are left out.

Some packs were made on Windows, which doesn't mind if a simfile names its music `Tell Me A Story.ogg` and the file is `Tell Me a Story.ogg`.
Web servers do mind, so such files are saved under the name the simfile uses.

## Adding a pack

1. Download the pack's zip.
2. From the repository root, run:

   ```
   python3 tools/make_pack.py <pack.zip> <id> <name> <source page URL>
   ```

   It writes the trimmed songs and `index.json` to `<id>/`, and adds the pack to `packs.json`.
3. Commit and push. GitHub Pages publishes the change within a few minutes.

Footnotes lists every pack in `packs.json` on its Songs page.

## Credits

Mintmania comes from the song pack published at [stepmaniaonline.net/pack/2636](https://stepmaniaonline.net/pack/2636).
Its charts are by Trick Master Mint and others.
[mintmania/README.md](mintmania/README.md) lists every song with its artist and its charts' descriptions.

## Rights

The music, charts and images belong to their creators, and are hosted here with permission for practice with Footnotes.
They aren't covered by an open license and may not be redistributed.
To ask for something to be removed, [open an issue](https://github.com/chihduo/footnotes-packs/issues).
