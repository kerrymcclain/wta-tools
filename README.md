# WTA Tools

Free tools from West Texas Analytics, LLC, published at **https://tools.westtexasanalytics.com** with GitHub Pages.

| Path | What it is |
|---|---|
| `/` | Landing page listing the tools |
| `/tax-code/` | Property Tax Code Search: visitors open the Comptroller's PDF in their own browser and search it. Nothing is uploaded. |

## When the Comptroller posts a new Tax Code PDF

The search tool reads `tax-code/edition.json` to know which copy is current. When a visitor's saved PDF is an older edition, or an older copy of the current edition, the tool shows a banner telling them to download the new file. To update it, edit only `tax-code/edition.json` (pencil icon on GitHub, then **Commit changes**):

```json
{
  "edition": 2025,
  "file": "96-297-25.pdf",
  "url": "https://comptroller.texas.gov/taxes/property-tax/docs/96-297-25.pdf",
  "bytes": 3228704,
  "posted": "2026-01-07"
}
```

- `edition`: the year printed on the cover ("TEXAS PROPERTY TAX CODE 2025 EDITION").
- `file` / `url`: the Comptroller's file name and download link.
- `bytes`: exact file size in bytes (Finder → Get Info, or the size from the download).
- `posted`: the date the Comptroller posted that file (YYYY-MM-DD).

The live site updates a minute or two after the commit.

## Files

- `CNAME`: custom domain for GitHub Pages (`tools.westtexasanalytics.com`). DNS is a CNAME record `tools` → `kerrymcclain.github.io` at GoDaddy.
- `.nojekyll`: serve the files as-is.
- `favicon-32.png`, `apple-touch-icon.png`: Twin Buttes site icon.
