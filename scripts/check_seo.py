"""Pre-push SEO/content quality gate for Kokeniwa articles."""
from __future__ import annotations
import argparse, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "content" / "blog"
# English articles use a 1,500-character minimum for changed posts.
# Longer pillar pages remain preferable, but this blocks genuinely thin drafts
# without making the existing 20-post archive impossible to maintain.
MIN_BODY = 1500

def parse_article(path):
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2) if text.startswith("---") else []
    raw, body = (parts[1], parts[2]) if len(parts) > 2 else ("", text)
    meta = {}
    for line in raw.splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m: meta[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return meta, body

def body_chars(body):
    body = re.sub(r"```.*?```", " ", body, flags=re.S)
    body = re.sub(r"!?(\[[^\]]*\])\([^)]*\)", r"\1", body)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"[#*_>`~-]", "", body)
    return len(re.sub(r"\s+", "", body))

def changed_paths(local, remote):
    if not local or set(local) == {"0"}: return set()
    base = f"{remote}..{local}" if remote and set(remote) != {"0"} else f"{local}^..{local}"
    try:
        out = subprocess.check_output(["git", "diff", "--name-only", base], cwd=ROOT, text=True)
    except subprocess.CalledProcessError: return set()
    return {Path(x.strip()).as_posix() for x in out.splitlines() if x.strip()}

def audit(pre_push_paths=None):
    errors, warnings, titles = [], [], {}
    for path in sorted(BLOG.glob("*.md")):
        rel = path.relative_to(ROOT).as_posix(); meta, body = parse_article(path)
        for key in ("title", "date", "description"):
            if not meta.get(key): errors.append(f"{rel}: missing front matter '{key}'")
        if meta.get("description") and not 50 <= len(meta["description"]) <= 180:
            errors.append(f"{rel}: description must be 50-180 chars (got {len(meta['description'])})")
        if meta.get("title"): titles.setdefault(meta["title"].casefold(), []).append(rel)
        chars = body_chars(body)
        if chars < MIN_BODY:
            msg = f"{rel}: body is {chars} chars (recommended minimum {MIN_BODY})"
            (errors if pre_push_paths and rel in pre_push_paths else warnings).append(msg)
        headings = len(re.findall(r"^#{2,3}\s+", body, flags=re.M))
        if headings < 2:
            msg = f"{rel}: add at least two descriptive H2/H3 headings (found {headings})"
            (errors if pre_push_paths and rel in pre_push_paths else warnings).append(msg)
        tokens = [t for t in re.split(r"[-_ ]+", path.stem.lower()) if len(t) > 2]
        haystack = (meta.get("title", "") + " " + body).lower()
        if tokens and not any(t in haystack for t in tokens if t not in {"the", "and", "for", "how", "with", "from"}):
            warnings.append(f"{rel}: slug terms are not visible in title/body")
    for title, paths in titles.items():
        if len(paths) > 1: errors.append(f"duplicate title: {', '.join(paths)}")
    return errors, warnings

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--pre-push", nargs=2, metavar=("LOCAL_SHA", "REMOTE_SHA")); args = ap.parse_args()
    paths = None
    if args.pre_push:
        changed = changed_paths(*args.pre_push)
        paths = {p for p in changed if p.startswith("content/blog/") and p.endswith(".md")}
        print(f"SEO gate (en): checking {len(paths)} changed article(s), {len(list(BLOG.glob('*.md')))} total")
    errors, warnings = audit(paths)
    for msg in warnings: print(f"WARN  {msg}")
    for msg in errors: print(f"ERROR {msg}")
    print(f"SEO gate: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0

if __name__ == "__main__": sys.exit(main())
