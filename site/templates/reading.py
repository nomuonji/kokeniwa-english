"""英文解釈問題のページ群（個別・一覧・カテゴリ別・難易度別）。"""
from lib import config
from lib.render import esc
from templates import layout

QUIZ_SCRIPT = '<script src="/static/quiz.js" defer></script>'


def level_of(problem):
    return config.DIFFICULTY_LEVELS[problem["difficulty"]]


def category_url(category):
    return f"/reading/category/{config.CATEGORY_SLUGS[category]}/"


def problem_url(problem):
    return f"/reading/{problem['id']}/"


def _badges(p, link_category=True):
    lv = level_of(p)
    cat = (f'<a class="badge badge-cat" href="{category_url(p["category"])}">{esc(p["category"])}</a>'
           if link_category else f'<span class="badge badge-cat">{esc(p["category"])}</span>')
    fmt = "選択式" if p["format"] == "quiz" else "和訳"
    return (f'<span class="badge badge-{lv["slug"]}">{lv["label"]}</span>'
            f'{cat}<span class="badge">{fmt}</span>')


def _list_items(problems):
    items = []
    for p in problems:
        items.append(
            f'<a class="list-item" href="{problem_url(p)}">'
            f'<div class="meta"><span class="num">No.{p["id"]}</span>{_badges(p, link_category=False)}'
            f'<span class="num">{esc(p["point"])}</span></div>'
            f'<div class="en">{esc(p["sentence_en"])}</div>'
            f'</a>')
    return "\n".join(items)


def _level_chips(problems, active_slug=None):
    chips = []
    all_cls = ' active' if active_slug is None else ''
    chips.append(f'<a class="chip{all_cls}" href="/reading/">すべて</a>')
    for d, lv in config.DIFFICULTY_LEVELS.items():
        n = sum(1 for p in problems if p["difficulty"] == d)
        cls = ' active' if lv["slug"] == active_slug else ''
        chips.append(f'<a class="chip{cls}" href="/reading/level/{lv["slug"]}/">'
                     f'{lv["label"]} {esc(lv["name"])}<span class="count">{n}</span></a>')
    return f'<div class="chip-row">{"".join(chips)}</div>'


def _category_chips(problems, active=None):
    counts = {}
    for p in problems:
        counts[p["category"]] = counts.get(p["category"], 0) + 1
    chips = []
    for cat, slug in config.CATEGORY_SLUGS.items():
        if cat not in counts:
            continue
        cls = ' active' if cat == active else ''
        chips.append(f'<a class="chip{cls}" href="/reading/category/{slug}/">'
                     f'{esc(cat)}<span class="count">{counts[cat]}</span></a>')
    return f'<div class="chip-row">{"".join(chips)}</div>'


def render_index(cfg, problems):
    content = f"""
<h1>英文解釈トレーニング</h1>
<p class="lead">一文をどこまで正確に読めるか。構文・語法・論理の急所を突く全{len(problems)}問。
1問1ページ、その場で答え合わせと解説が読めます。</p>
<h2>レベルで選ぶ</h2>
{_level_chips(problems)}
<h2>カテゴリで選ぶ</h2>
{_category_chips(problems)}
<h2>全問題</h2>
{_list_items(problems)}
"""
    return layout.page(
        cfg, title="英文解釈トレーニング",
        description=f"B2〜C2レベルの英文解釈問題{len(problems)}問。構文把握・倒置・省略など21カテゴリ。1問ごとに詳しい解説つき。",
        path="/reading/", content=content,
        breadcrumbs=[("/reading/", "英文解釈")], active_nav="/reading/")


def render_level(cfg, problems, difficulty):
    lv = config.DIFFICULTY_LEVELS[difficulty]
    subset = [p for p in problems if p["difficulty"] == difficulty]
    path = f"/reading/level/{lv['slug']}/"
    content = f"""
<h1>英文解釈 {lv['label']}（{esc(lv['name'])}）</h1>
<p class="lead">{esc(lv['description'])} 全{len(subset)}問。</p>
{_level_chips(problems, active_slug=lv['slug'])}
{_list_items(subset)}
"""
    return layout.page(
        cfg, title=f"英文解釈 {lv['label']}（{lv['name']}）",
        description=f"{lv['label']}レベルの英文解釈問題{len(subset)}問。{lv['description']}",
        path=path, content=content,
        breadcrumbs=[("/reading/", "英文解釈"), (path, lv["label"])],
        active_nav="/reading/")


def render_category(cfg, problems, category):
    slug = config.CATEGORY_SLUGS[category]
    subset = [p for p in problems if p["category"] == category]
    path = f"/reading/category/{slug}/"
    content = f"""
<h1>英文解釈「{esc(category)}」</h1>
<p class="lead">「{esc(category)}」を扱う問題 全{len(subset)}問。</p>
{_category_chips(problems, active=category)}
{_list_items(subset)}
"""
    return layout.page(
        cfg, title=f"英文解釈「{category}」の問題一覧",
        description=f"「{category}」がテーマの英文解釈問題{len(subset)}問。1問ごとに和訳と詳しい解説つき。",
        path=path, content=content,
        breadcrumbs=[("/reading/", "英文解釈"), (path, category)],
        active_nav="/reading/")


def _answer_panel_body(p):
    return f"""
<h2>全文訳</h2>
<p>{esc(p["translation_ja"])}</p>
<h2>解説</h2>
<p>{esc(p["explanation_ja"])}</p>
"""


def render_problem(cfg, problems, index):
    p = problems[index]
    lv = level_of(p)
    path = problem_url(p)
    panel_id = f"answer-{p['id']}"

    if p["format"] == "quiz":
        choices = "".join(
            f'<li><button type="button" class="choice" data-index="{i}">'
            f'<span class="marker">{chr(65 + i)}</span><span class="label">{esc(c)}</span>'
            f'</button></li>'
            for i, c in enumerate(p["choices"]))
        interaction = f"""
<p class="question-ja">Q. {esc(p["question_ja"])}</p>
<ul class="choices">{choices}</ul>
<p class="verdict" role="status"></p>
<div class="answer-panel" id="{panel_id}">{_answer_panel_body(p)}</div>
"""
        quiz_attrs = f' data-quiz data-answer="{p["answer_index"]}"'
    else:
        interaction = f"""
<p class="question-ja">Q. {esc(p["question_ja"])}</p>
<p><button type="button" class="reveal-btn" data-reveal="{panel_id}">訳と解説を表示</button></p>
<div class="answer-panel" id="{panel_id}">{_answer_panel_body(p)}</div>
"""
        quiz_attrs = ""

    prev_link = next_link = ""
    if index > 0:
        q = problems[index - 1]
        prev_link = (f'<a class="prev" href="{problem_url(q)}">'
                     f'<span class="dir">← 前の問題</span>No.{q["id"]} {esc(q["point"])}</a>')
    if index < len(problems) - 1:
        q = problems[index + 1]
        next_link = (f'<a class="next" href="{problem_url(q)}">'
                     f'<span class="dir">次の問題 →</span>No.{q["id"]} {esc(q["point"])}</a>')

    content = f"""
<h1>英文解釈 No.{p["id"]}</h1>
<article class="quiz"{quiz_attrs}>
  <div class="quiz-meta">{_badges(p)}<span class="badge">{esc(p["point"])}</span></div>
  <p class="sentence-en" lang="en">{esc(p["sentence_en"])}</p>
  {interaction}
</article>
<nav class="pager">{prev_link}{next_link}</nav>
"""
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Quiz",
        "name": f"英文解釈 No.{p['id']}: {p['point']}",
        "educationalLevel": lv["label"],
        "about": p["category"],
        "inLanguage": "ja",
    }
    return layout.page(
        cfg, title=f"英文解釈 No.{p['id']}｜{p['category']}「{p['point']}」",
        description=f"【{lv['label']}】{p['sentence_en'][:80]} — {p['question_ja']} 和訳と詳しい解説つき。",
        path=path, content=content, jsonld=jsonld,
        breadcrumbs=[("/reading/", "英文解釈"),
                     (category_url(p["category"]), p["category"]),
                     (path, f"No.{p['id']}")],
        active_nav="/reading/", extra_scripts=QUIZ_SCRIPT)
