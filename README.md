# gmaps-list-export 🗺️→📄

Export a **Google Maps shared/saved place list** to CSV, Markdown or JSON.

```bash
python gmaps_list_export.py --url "https://maps.app.goo.gl/xxxxx" -o tokyo.csv
```

```
index,name,lat,lng,url
1,一蘭拉麵 新宿店,35.6938,139.7036,https://www.google.com/maps/place/...
2,teamLab Planets TOKYO,35.6494,139.7906,https://www.google.com/maps/place/...
...
```

> 中文說明見下方 [中文](#中文說明)

---

## Why

Google Maps lets you build and share a saved list, but gives you **no way to get the places back out**. There is no export button and no public API for saved lists. The list is lazy-loaded into a virtualised sidebar, so you cannot select-all-and-copy either — scroll away and the DOM nodes are gone.

Which is annoying the moment you want to do anything with the list: plan a route, sort by area, hand it to a spreadsheet, feed it to something else. This drives a real browser, scrolls the sidebar until nothing new loads, and writes the whole thing to a file.

Originally built to get a 432-place Tokyo list out of Maps and into a planning spreadsheet.

## Install

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
# CSV (default)
python gmaps_list_export.py --url "<list url>" -o kyoto.csv

# Markdown table, with a title
python gmaps_list_export.py --url "<list url>" -o kyoto.md --title "Kyoto 2-day"

# everything at once — writes kyoto.csv, kyoto.md, kyoto.json
python gmaps_list_export.py --url "<list url>" -o kyoto --format all
```

| Flag | Default | Notes |
|---|---|---|
| `--url` | *required* | Google Maps shared list URL (`maps.app.goo.gl/...` short links work) |
| `-o, --output` | `places.csv` | extension decides the format unless `--format` is set |
| `-f, --format` | from extension | `csv` / `md` / `json` / `all` |
| `--title` | `Google Maps list` | heading for Markdown output |
| `--headless` | off | see caveat below |
| `--locale` | `zh-TW` | browser locale — affects the language of place names |
| `--scroll-pause` | `1.5` | seconds between scrolls; raise it on a slow connection |

## Output

CSV is written as **UTF-8-sig** so Excel on Windows opens CJK place names without mojibake.

| Column | Notes |
|---|---|
| `index` | 1-based position in the list |
| `name` | place name as Maps renders it in `--locale` |
| `lat` / `lng` | parsed from the place URL when present, otherwise blank |
| `url` | canonical Google Maps place link |

## Caveats

- **`--headless` usually does not work.** Maps detects it and never populates the sidebar, so you get zero places. The default is a visible browser window; let it scroll and do not interact with it.
- Scraping depends on Maps' DOM. Google changes it periodically — if you suddenly get 0 results, the sidebar selector in `_SIDEBAR_SELECTORS` is the first thing to check.
- Coordinates come from the `!3d…!4d…` fragment of the place URL. Maps does not always include it; those rows get blank `lat`/`lng`.
- The list must be **publicly shared**. Private lists need a logged-in session, which this does not handle.
- Be reasonable about how often you run this.

## License

MIT — see [LICENSE](LICENSE).

---

## 中文說明

把 **Google Maps 的共享清單／收藏清單匯出成 CSV、Markdown 或 JSON**。

**為什麼需要它**：Google Maps 可以建立和分享收藏清單，但**完全沒有匯出功能**，也沒有公開 API。清單是懶載入到虛擬化側邊欄裡的，滾過去 DOM 就被回收，連全選複製都做不到。於是你想拿這份清單做任何事（排行程、依區域分類、丟進試算表）都卡住。

這支工具開一個真實瀏覽器，自動滾動側邊欄直到沒有新地點載入，然後把全部結果寫成檔案。原本是為了把一份 432 個地點的東京清單弄進試算表而寫的。

**安裝**：`pip install -r requirements.txt` 然後 `playwright install chromium`

**使用**：
```bash
python gmaps_list_export.py --url "<清單網址>" -o tokyo.csv
python gmaps_list_export.py --url "<清單網址>" -o tokyo --format all   # csv + md + json 都出
```

**注意**：
- `--headless` 多半沒用——Maps 偵測得到，側邊欄不會載入，會抓到 0 筆。預設就是開可見視窗，讓它自己滾，中途不要動它。
- CSV 用 UTF-8-sig 輸出，Windows 的 Excel 開中文地名不會亂碼。
- 靠 DOM 結構抓資料，Google 改版就可能失效；抓到 0 筆時先檢查 `_SIDEBAR_SELECTORS`。
- 清單必須是**公開分享**的，私人清單需要登入狀態，本工具不處理。
