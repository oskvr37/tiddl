# 📝 File Templating

Templates are text strings that describe folder and file structure.
They use placeholders (in `{curly_braces}`) that get replaced with actual metadata values from:

- **Track / Video** → `item`
- **Album** → `album`
- **Playlist** → `playlist`
- Plus any **custom fields**

A template like:

```
{album.artist}/{album.title}/{item.title}
```

becomes this:

```
Daft Punk/Discovery/Harder Better Faster Stronger
```

---

## 🧩 Template Variables

Each object type exposes fields you can use inside templates.

### `item` (Track or Video)

| Field                        | Description                            | Example                         | Type |
| ---------------------------- | -------------------------------------- | ------------------------------- | ---- |
| `item.id`                    | Track/Video ID                         | `123456`                        | int  |
| `item.title`                 | Title                                  | `Harder Better Faster Stronger` | str  |
| `item.title_version`         | Title + version (if present)           | `One More Time (Radio Edit)`    | str  |
| `item.number`                | Track number                           | `3`                             | int  |
| `item.volume`                | Disc/volume number                     | `1`                             | int  |
| `item.version`               | Version string (track only)            | `Remastered`                    | str  |
| `item.copyright`             | Copyright info (track only)            | `© 2023 Sony Music`             | str  |
| `item.bpm`                   | Beats per minute (if available)        | `120`                           | int  |
| `item.isrc`                  | ISRC code (track only)                 | `USQX91501234`                  | str  |
| `item.quality`               | Audio/video quality                    | `HIGH`                          | str  |
| `item.artist`                | Primary artist name                    | `Daft Punk`                     | str  |
| `item.artists`               | All main artists                       | `Daft Punk, Pharrell Williams`  | str  |
| `item.features`              | Featured artists                       | `Pharrell Williams`             | str  |
| `item.artists_with_features` | Main + featured artists                | `Daft Punk, Pharrell Williams`  | str  |
| `item.explicit`              | Explicit content                       | `E`                             | str  |
| `item.dolby:(Dolby Atmos)`   | Dolby Atmos (track only, `UserFormat`) | `(Dolby Atmos)`                 | str  |

---

### `album`

| Field                | Description                         | Example      | Type     |
| -------------------- | ----------------------------------- | ------------ | -------- |
| `album.id`           | Album ID                            | `98765`      | int      |
| `album.title`        | Album title                         | `Discovery`  | str      |
| `album.artist`       | Primary artist                      | `Daft Punk`  | str      |
| `album.artists`      | All main artists                    | `Daft Punk`  | str      |
| `album.date`         | Release date                        | `2001-03-13` | datetime |
| `album.explicit`     | Explicit content                    | `clean`      | str      |
| `album.master:[MAX]` | Is album max quality (`UserFormat`) | `[MAX]`      | str      |

---

### `playlist`

| Field              | Description                    | Example               | Type     |
| ------------------ | ------------------------------ | --------------------- | -------- |
| `playlist.uuid`    | Playlist unique ID             | `b8f1d9f8-...`        | str      |
| `playlist.title`   | Playlist name                  | `My Favorites`        | str      |
| `playlist.index`   | Track index within playlist    | `5`                   | int      |
| `playlist.created` | Creation date (`datetime`)     | `2024-01-15 10:42:00` | datetime |
| `playlist.updated` | Last updated date (`datetime`) | `2024-03-02 09:00:00` | datetime |

> [!NOTE]
> Tidal API does not provide full album data for playlist tracks,
> if you are downloading a playlist with template that contains `{album...}`,
> then `tiddl` is making additional request to the API to fetch album data for a track.
> The download may take a little longer but it's not a big deal - just one more request for every playlist track.
> If there are multiple tracks from the same album, then the album data is cached locally,
> and there is only one request per album. Related issue: #217

---

### Explicit

| Format           | True Value | False Value |
| ---------------- | ---------- | ----------- |
| `.explicit`      | E          |             |
| `.explicit:long` | explicit   |             |
| `.explicit:full` | explicit   | clean       |

### User Format

You can format `UserFormat` fields how you want:

| Format                       | True Value    | False Value |
| ---------------------------- | ------------- | ----------- |
| `item.dolby:D`               | D             |             |
| `item.dolby:DOLBY`           | DOLBY         |             |
| `item.dolby:dolby`           | dolby         |             |
| `album.master:(Max Quality)` | [Max Quality] |             |

### `extra` and `custom` fields

You can also use:

- `now` → current datetime
- Any key passed as `extra` in code.

---

## 🧼 Sanitization

All template segments are sanitized:

- Invalid filesystem characters are removed or replaced.
- Empty placeholders are skipped cleanly.
- Each path component is treated separately (split by `/`).

---

## ⚙️ Configuration Example

Your `[templates]` section in `config.toml` defines templates per media type.

```toml
[templates]
default = "{album.artist}/{album.title}/{item.title}"
track = "tracks/{item.id}"
video = "videos/{item.title}"
album = "artists/{album.artist}/{album.title}/{item.title}"
playlist = "{playlist.title}/{playlist.index}. {item.artist} - {item.title}"
mix = "mixes/{mix_id}/{item.artist} - {item.title}"
```

If no specific template is set, the `default` one is used.

---

## 🧠 Tips

- You can format datetime fields, e.g. `{album.date:%Y-%m-%d}`.
- You can build nested folders safely using `/` separators.
- You can format string and integer fields, [learn more](https://www.pythonmorsels.com/string-formatting/#floating-point-numbers-and-integers)

## 🖥️ Source Code

Source code is located at [`/tiddl/core/utils/format.py`](/tiddl/core/utils/format.py)
