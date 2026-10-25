# WTA Tools tests

Browser tests for the tools site. Each test starts a local web server on a temporary copy of the repo and drives headless Chromium with Playwright.

```bash
pip install -r tests/requirements.txt
python -m playwright install chromium
python tests/run_all.py                                  # everything except the real-PDF test
python tests/run_all.py --pdf ~/Downloads/96-297-25.pdf  # also runs the test that needs the Comptroller's PDF
```

| Test | Covers |
|---|---|
| `test_tax_code.py` | Tax Code Search: edition detection and banners, result badges (1–99), badge overlay in the PDF, dismissing the notice, phone layout. Uses small stand-in PDFs from `make_test_pdf.py`. |
| `test_tax_code_clear.py` | Tax Code Search with the real PDF: clearing a search returns to page 1; typing while browsing keeps your place. |
| `test_tax_calendar.py` | Tax Calendar: weekend and holiday rollover (including Dec. 31 into January), leap years, even-year entries, audience and key-date filters, section links, `.ics` export and line folding, phone layout. |
| `test_categories.py` | Property Categories: search ranking for plain-English descriptions, code lookups, cross-links between categories, filters, deep links (`#J3`), phone layout. |

Run them after any change to a tool, and add a check when you fix a bug. Screenshots are written to `tests/.out/`.
