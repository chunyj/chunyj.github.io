#!/usr/bin/env python3
"""Sync _bibliography/papers.bib with new publications from Semantic Scholar.

Fetches the author's paper list from the Semantic Scholar API and appends
any entries not already present (matched by arXiv id / DOI / normalized
title) to _bibliography/papers.bib. Existing entries are never modified,
so hand-tuned fields (abbr, preview, selected, ...) are preserved.

New entries are appended with a best-effort guess at the fields and a
`needs_review = {true}` marker so they can be spotted and polished
(preview image, abbr, selected flag) in the Jekyll site.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

AUTHOR_ID = "2350512621"  # Jina Chun, https://www.semanticscholar.org/author/2350512621
API_URL = (
    f"https://api.semanticscholar.org/graph/v1/author/{AUTHOR_ID}/papers"
    "?fields=title,year,venue,externalIds,authors,publicationDate"
)
BIB_PATH = Path(__file__).resolve().parent.parent / "_bibliography" / "papers.bib"


def fetch_papers():
    req = urllib.request.Request(API_URL, headers={"User-Agent": "publications-sync-script"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["data"]


def normalize_title(title):
    return re.sub(r"[^a-z0-9]", "", title.lower())


def existing_identifiers(bib_text):
    arxiv_ids = set(re.findall(r"arXiv[:.](\d{4}\.\d{4,5})", bib_text, re.IGNORECASE))
    dois = set(m.lower() for m in re.findall(r"doi\s*=\s*\{([^}]+)\}", bib_text, re.IGNORECASE))
    titles = set(
        normalize_title(m) for m in re.findall(r"title\s*=\s*\{([^}]+)\}", bib_text, re.IGNORECASE)
    )
    return arxiv_ids, dois, titles


def name_to_bibtex(full_name):
    parts = full_name.strip().split()
    if len(parts) < 2:
        return full_name
    last = parts[-1]
    first = " ".join(parts[:-1])
    return f"{last}, {first}"


def make_key(first_author_name, year, title):
    parts = first_author_name.strip().split()
    last = re.sub(r"[^a-z]", "", parts[-1].lower()) if parts else "unknown"
    words = re.findall(r"[a-zA-Z]+", title.lower())
    stop = {"a", "an", "the", "of", "for", "on", "in", "to", "and", "is", "an", "with"}
    first_word = next((w for w in words if w not in stop), (words[0] if words else "paper"))
    return f"{last}{year}{first_word}"


def build_entry(paper, existing_keys):
    title = paper["title"]
    year = paper.get("year") or "n.d."
    authors = " and ".join(name_to_bibtex(a["name"]) for a in paper.get("authors", []))
    ext = paper.get("externalIds") or {}
    arxiv_id = ext.get("ArXiv")
    doi = ext.get("DOI")

    if arxiv_id:
        journal = f"arXiv preprint arXiv:{arxiv_id}"
        abbr = "arXiv"
    else:
        journal = paper.get("venue") or "Preprint"
        abbr = journal[:20]

    first_author = paper["authors"][0]["name"] if paper.get("authors") else "unknown"
    key = make_key(first_author, year, title)
    base_key = key
    i = 2
    while key in existing_keys:
        key = f"{base_key}{i}"
        i += 1
    existing_keys.add(key)

    lines = [f"@article{{{key},", f"  abbr={{{abbr}}},", f"  title={{{title}}},"]
    if authors:
        lines.append(f"  author={{{authors}}},")
    lines.append(f"  journal={{{journal}}},")
    if doi:
        lines.append(f"  doi={{{doi}}},")
    lines.append(f"  year={{{year}}},")
    lines.append("  needs_review={true},")
    lines.append("}")
    return "\n".join(lines)


def main():
    bib_text = BIB_PATH.read_text()
    arxiv_ids, dois, titles = existing_identifiers(bib_text)
    existing_keys = set(re.findall(r"@\w+\{([^,]+),", bib_text))

    papers = fetch_papers()
    new_entries = []
    for paper in papers:
        ext = paper.get("externalIds") or {}
        arxiv_id = ext.get("ArXiv")
        doi = (ext.get("DOI") or "").lower()
        norm_title = normalize_title(paper["title"])

        if arxiv_id and arxiv_id in arxiv_ids:
            continue
        if doi and doi in dois:
            continue
        if norm_title in titles:
            continue

        new_entries.append(build_entry(paper, existing_keys))

    if not new_entries:
        print("No new publications found.")
        return

    addition = "\n\n" + "\n\n".join(new_entries) + "\n"
    with BIB_PATH.open("a") as f:
        f.write(addition)

    print(f"Added {len(new_entries)} new publication(s):")
    for entry in new_entries:
        first_line = entry.splitlines()[0]
        print(f"  - {first_line}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error syncing publications: {e}", file=sys.stderr)
        sys.exit(1)
