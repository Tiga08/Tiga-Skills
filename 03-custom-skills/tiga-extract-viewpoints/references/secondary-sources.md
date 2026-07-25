# Secondary-source fallback

Read this file **only** when Phase 4 has established that the primary text cannot be obtained. It is a degraded mode, not a shortcut: everything produced under it is explicitly labelled so a reader can tell reconstructed positions from quoted ones.

## Trigger and opt-out

Enter this mode when all of the following hold:

1. Every route in [source-routing.md](source-routing.md) for this source type has been tried and failed, or no route exists (audio-only with no transcript is the canonical case).
2. The failure is about the text being unavailable — not about a paywall, DRM, or login wall you were asked to bypass. Access controls are respected, not routed around.
3. `--no-secondary` was **not** passed.

With `--no-secondary`, deliver the acquisition gap report and stop. Do not produce a viewpoint document.

This mode applies to every source type — PDF, EPUB, Blog, Podcast. Podcasts hit it most often, because a show with no published transcript leaves no local route to its content.

Before searching, tell the user in one line that the primary text was unobtainable and that the output will be a secondary reconstruction.

## Search strategy by source type

Build queries from what is verified about the source — exact title, author or host names, guest names, publication or episode date, publisher or show name. Never seed a query with a claim you are trying to confirm; that retrieves the echo of your own guess.

**Podcast**

- Official episode page and show notes; the show's own site rather than an aggregator.
- Published transcript mirrors and community transcript archives.
- Articles the guest wrote on the same topic in the same period, and other interviews they gave about it.
- Coverage by credible outlets that quote the episode directly.
- Queries: `"<show name>" "<episode title>" transcript`, `"<guest name>" "<key topic>" interview <year>`, `"<guest name>" "<distinctive phrase from show notes>"`.

**Blog**

- Mirrors, syndicated reprints, and the author's own cross-posts.
- The same author stating the same position on another platform.
- Archive snapshots of the original URL.
- Queries: `"<exact title>" <author>`, `site:web.archive.org <url>`, `"<distinctive sentence from the excerpt>"`.

**PDF / EPUB**

- The publisher's book or paper page, including any official excerpt or sample chapter.
- Author interviews, talks, and conference recordings covering the same argument.
- Substantive reviews and quoted excerpts from credible outlets.
- For papers: the original venue, preprint server, or DOI landing page — a missing PDF often has an accessible abstract and citation record.
- Queries: `"<book title>" <author> excerpt`, `"<book title>" review`, `<author> "<central concept>" talk OR lecture`.

## Acceptance rules

- **Two independent sources per attributed claim.** Independent means different publishers and different authorship — a syndicated copy, an aggregator scrape, and the original are one source, not three. A claim supported by only one source is kept but tagged `single-source`.
- **Never reconstruct wording.** A secondary source establishes that a position was held, not how it was phrased. Do not present paraphrase as quotation, and do not quote a secondary source's paraphrase as the author's words.
- **Never fabricate locators.** No invented page numbers, chapter names, or timestamps. The locator field holds the secondary source's URL, plus its publisher and date.
- **Keep the reporting layer visible.** "Reported by X as saying Y" is not the same as "said Y". Where sources conflict, record the disagreement instead of picking the more convenient version.
- **Preserve tier through synthesis.** A reasoning chain assembled from secondary fragments is an inference about the argument, not the argument itself — mark it as such, and do not fill gaps between fragments with plausible connective steps.
- **Stop when the record is too thin.** If searching yields only titles, blurbs, and marketing copy, say so and deliver the gap report. A document built on nothing is worse than no document.

## Output constraints

- Open the document with a prominent notice, immediately under the title: the primary text was unavailable, what was tried, and that the content below is reconstructed from external sources.
- Set frontmatter `source_fidelity` to `secondary-only`, or to `mixed` when part of the primary text was obtained. `evidence_basis` names the actual basis.
- Every viewpoint entry carries its `tier` and, for secondary entries, the source links backing it.
- Include a "source fidelity and search record" section listing: the primary routes attempted and how they failed, every secondary source used with its link and date, and — explicitly — **what was searched for but not found**. The unfound scope is what tells a reader where the reconstruction is thinnest.
- Do not carry the template's precise-locator conventions (`[p.42]`, `[01:12:08]`) into secondary content. Those formats assert a precision this mode does not have.
