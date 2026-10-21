# Search entry improvement — 2026-10-21 JST

## Reader task and hypothesis
- Site: https://en.kokeniwa.net/
- Existing article: /blog/inanimate-subject/
- Intended query family (editorial hypothesis, not measured search volume): 無生物主語 訳し方 / 無生物主語 練習問題.
- Preserve the existing URL. Answer the question at the start, explain contrasts with original examples, and include five practice questions with answer reasons. Link to an existing exercise category and related explanations.
- Improve /vocab/ in place with real vocabulary previews rendered in HTML and explicit links into the existing trainer. Do not create thin word or query-variant pages.
- The home title now describes the actual material. Article `updated` is distinct from the original publication date and feeds visible text and BlogPosting.dateModified.

## Scope and evidence
- Data examples come from the repository's current vocabulary data; counts are calculated from the same loaded data as the trainers. Previews expose words/meanings already public, not Kindle-only explanation or bonus material.
- Full trainers, mature sets and Kindle bonuses retain their existing noindex policy. Neither sitemap inclusion nor indexation of those pages is changed.
- Japanese grammar: Japan Foundation, Irodori bilingual grammar notes, Starter lessons 3 and 5: https://www.irodori.jpf.go.jp/assets/data/Grammar_all.pdf . Discourse reference: https://arxiv.org/abs/cmp-lg/9609006 . Topic/omission and 好き are checked separately; context-dependent practice examples are original.
- JLPT vocabulary grouping caveat: official FAQ https://www.jlpt.jp/e/faq/index.html . These sets are not represented as the official exhaustive word lists.
- English verb patterns: https://learnenglish.britishcouncil.org/free-resources/grammar/english-grammar-reference/verbs-followed-infinitive . Japanese translations and exercises are original; no rule requires every inanimate subject to be paraphrased.
- Search engine sampling on 2026-10-21 found existing question URLs on both hosts; it does not establish complete index coverage.
- Sites Operator registry and planning-digest reads returned Firestore 429/INVALID_ARGUMENT. GSC impressions, clicks, CTR and rankings were not available. No numeric traffic baseline or ranking improvement is claimed.
- Editorial review: self-review for factual consistency, query intent, redundancy, exercises and existing product boundaries. Independent reviewer not used.

## Validation and follow-up
- Run python site/build_site.py (all generated-page internal links), python -m compileall -q site, and the existing scripts/check_seo.py. Pre-existing unrelated SEO warnings are not silently treated as fixed.
- Verify /, /vocab/, /blog/inanimate-subject/ have the production canonical and no noindex; trainers and reader bonuses must retain noindex.
- Browser check: readable static samples with JavaScript disabled; desktop and mobile widths; vocabulary sample links must open the intended flipped card.
- Delivery evidence: PR and CI are recorded in the GitHub history. Generated dist is synchronized by the existing Publish generated dist workflow after merge; verify public HTML separately.
- When analytics are available, compare these existing URLs' next 28 complete days with the preceding 28 days (query family and page-level impressions, clicks, CTR and average position). Also inspect query-matched landings into the practice tools. Annotate the date; do not attribute all changes to this one edit or claim causality from low counts.
- No new schedule, database or external service was added. Rollback is a revert of the delivery PR.
