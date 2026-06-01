#!/usr/bin/env python3

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOGS_DIR = ROOT / "blogs"
OUTPUT_PATH = BLOGS_DIR / "index.html"
INDEX_LIST_PATTERN = re.compile(
    r'(<ul id="blog-list"[^>]*>)(.*?)(</ul>)', flags=re.IGNORECASE | re.DOTALL
)


@dataclass(frozen=True)
class BlogPost:
    filename: str
    title: str
    modified: datetime

    @property
    def link(self) -> str:
        return self.filename


def friendly_title(stem: str) -> str:
    return re.sub(r"[_-]+", " ", stem).strip().title() or stem


def extract_title(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    match = re.search(r"<title>(.*?)</title>", content, flags=re.IGNORECASE | re.DOTALL)
    if match:
        title = re.sub(r"\s+", " ", match.group(1)).strip()
        if title:
            return title
    heading = re.search(
        r"<h1[^>]*>(.*?)</h1>", content, flags=re.IGNORECASE | re.DOTALL
    )
    if heading:
        title = re.sub(r"<[^>]+>", "", heading.group(1))
        title = re.sub(r"\s+", " ", title).strip()
        if title:
            return title
    return friendly_title(path.stem)


def read_posts() -> list[BlogPost]:
    posts: list[BlogPost] = []
    for path in BLOGS_DIR.glob("*.html"):
        if path.name == OUTPUT_PATH.name:
            continue
        posts.append(
            BlogPost(
                filename=path.name,
                title=extract_title(path),
                modified=datetime.fromtimestamp(path.stat().st_mtime),
            )
        )
    posts.sort(key=lambda post: (post.modified, post.title.lower()), reverse=True)
    return posts


def render(posts: list[BlogPost]) -> str:
    items = []
    for post in posts:
        items.append(f"""        <li class="archive-item">
                    <a class="archive-card" href="{html.escape(post.link)}">
                        <span class="archive-meta">{post.modified:%b %d, %Y}</span>
                        <span class="archive-title">{html.escape(post.title)}</span>
                        <span class="archive-link">Read article</span>
          </a>
        </li>""")

    if not items:
        items.append("""        <li class="archive-empty">
                    <span class="archive-meta">No posts yet</span>
          <p>Add an HTML file under blogs/ and this index will list it automatically.</p>
        </li>""")

    items_html = "\n".join(items)

    source = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
    if source:
        match = INDEX_LIST_PATTERN.search(source)
        if not match:
            raise ValueError('Could not find <ul id="blog-list"> in blogs/index.html')
        return INDEX_LIST_PATTERN.sub(rf"\1\n{items_html}\n      \3", source, count=1)

    raise FileNotFoundError(
        "blogs/index.html must exist before generating the blog list"
    )


def main() -> None:
    OUTPUT_PATH.write_text(render(read_posts()), encoding="utf-8")


if __name__ == "__main__":
    main()
