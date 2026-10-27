# Assignment Control: COM7022

## Identity

- Module: COM7022 Machine Learning
- Assignment: COM7022 Assignment [5444], Portfolio (Task 1 Practical Project + Task 2 Critical Report)
- Student ID: 25199053
- Tutor: not named; in-class feedback recorded in `_brain/TUTOR_FEEDBACK.md` (2026-10-27). ROC: tutor confirmed (2026-10-27) it is not required for this clustering project.
- Deadline: ~2026-11-17 (student, 2026-10-24: "24 days from now"); confirm exact time on iLearn
- GitHub: https://github.com/kvmmn/_COM7022_MachineLearning (module folder = repo root, as COM7021); GitHub Pages `index.html` = visual draft review
- Assessed run: Google Colab, executed and saved to GitHub 2026-10-27 (commit 8acdcc8); all numbers reproduce the local run (see decision log D15)
- Palette: Arden Midnight/Tiffany (`COM7021 - Assignment/VISUAL_DESIGN_GUIDE.md`)
- Final filename (proposed): `COM7022_Portfolio_25199053_final.docx` (+ `.pdf`)

## Authoritative materials

| Source | File or link | Version/date | Read fully | Key authority |
|---|---|---|---|---|
| Brief | `[5444] -Machine Learning - COM7022.pdf` | [5444] | Yes | Two tasks, 3000 words, 60/40 split, LO1-LO3 |
| Rubric | `_brain/COM7022_RUBRIC.md` (supplied by student 2026-10-24) | iLearn | Yes | Single holistic scale; top bands reward correct import, pre-processing, descriptive statistics, correct ML methodology, all processes correct, exceptional judgement |
| Tutor notes | `_brain/TUTOR_FEEDBACK.md` (in-class feedback, 2026-10-27) | 2026-10-27 | Yes | Report structure, screenshots, captions with repo paths, flowcharts |
| Dataset | `Sales-[5444].csv` | 1000 rows x 10 cols | Profiled | Only authorised dataset |
| Lessons | `COM7022 - Lessons/` L2 (prep, PCA, min-max), L8 (K-Means, elbow, inertia, DBSCAN activity), L9 (hierarchical, 4 linkages, dendrogram, fcluster) | - | Scanned | Taught vocabulary and toolset |
| Code Space | `Python_Codes/` (Kmeans, KNN, Decision Tree, Colab-style notebooks) | - | Not yet | Taught code style |
| eBook | Müller & Guido, *Intro to ML with Python* | - | Reference | Core citation for clustering + evaluation |
| AI policy | Linked from brief | - | No | Declaration requirement |
| Referencing | Arden Harvard | - | - | Citation style |

## Task contract

- Scenario and audience: Student is a new ML Analyst at a fast-growing e-commerce company. Task 1 audience = marker/technical reviewer. Task 2 audience = **executive, non-technical stakeholders**.
- Decision or problem: group products by characteristics and sales performance with unsupervised clustering, pick the most suitable model, and turn clusters into business actions.
- Required task verbs (Task 1): prepare, select and justify features, apply multiple clustering techniques (K-Means, Hierarchical, DBSCAN), evaluate suitability, use dimensionality reduction (PCA) where appropriate, evaluate and compare with performance/validation measures, justify most suitable model (technical + business), analyse and describe cluster characteristics.
- Required task verbs (Task 2): evaluate suitability (incl. feature selection, model development decisions), compare performance and effectiveness (strengths, limitations, suitability), justify final model (technical + business), present for non-technical stakeholders with visualisations, interpretation, evidence-based recommendations.
- Required deliverables and order: **one** Word or PDF document containing Task 1 and Task 2; screenshot evidence of all processes and results; Task 1 code in an appendix; student ID visible.
- Required methods: Python only; notebook with clean code, adequate comments, informative visualisations.
- Out of scope: supervised models as the main deliverable; claiming causal effects from clusters.
- Referencing style: Arden Harvard.
- Word-count rule: 3000 words total. Task 1 = 2000 words *equivalence* (coded work, 60 marks), Task 2 = 1000 words (critical report, 40 marks). Proposed Stage 0 convention: counted = Task 1 + Task 2 body prose; excluded = cover, contents, captions, tables, references, appendix code. **To confirm.**
- Submission format: .docx / .pdf.

## Dataset sanity check (2026-10-24)

| Fact | Value |
|---|---|
| Rows / columns | 1000 / 10 (eBay-style men's fragrance listings) |
| Full-row duplicates | 0 |
| Missing | price 5, available 111, sold 8, lastUpdated 53, Catatory 3, text 3, Item_Name 1, priceWithCurrency 1 |
| Recoverable | All 5 missing `price` from `priceWithCurrency`; 2 of 8 `sold` from `text`; `available` NaN = "Limited quantity" (59), "Last One" (47), lots (2) |
| Censoring | 296 rows "More than 10 available" stored as 10 |
| Currency | 996 US$, 3 C$ |
| price | 3 to 259.09, median 35.71 |
| sold | 1 to 54,052, median 49.5, mean 775 (extreme right skew → log transform) |
| Category | ~20 dirty labels (case/spelling variants of EDT/EDP/Cologne/Parfum) → normalise to ~6 groups |
| Brand | `Item_Name`; long tail, "Unbranded" 39 |
| Location | US 912, Hong Kong 52, other ~36 |
| Dates | Mostly Apr-May 2024, mixed month formats; `lastUpdated` = listing recency, not sales date |

Expected result range: 3 to 5 K-Means clusters (e.g. budget slow-sellers, mid-price steady, premium, viral best-sellers); silhouette likely modest (0.25 to 0.45) because listings form a continuum; DBSCAN likely isolates the extreme best-sellers as noise. A low silhouette is a legitimate finding, not a failure.

## Proposed structure

| Section/artifact | Purpose | LO | Evidence | Target words |
|---|---|---:|---|---:|
| Cover + contents | ID, module, word count | - | - | 0 |
| **Task 1** | | | | **2000** |
| 1.1 Problem framing and data understanding | Scenario, unit of observation, EDA | 1 | profile table, distributions | 250 |
| 1.2 Data preparation | cleaning, recovery from text, censoring, category normalisation, outliers, log + scaling | 1,2 | decision log, before/after table | 350 |
| 1.3 Feature selection and justification | candidate vs selected features, correlation, variance | 2 | correlation heatmap, feature table | 250 |
| 1.4 PCA | explained variance, 2D projection | 2 | scree + biplot | 150 |
| 1.5 K-Means | elbow + silhouette for k, fit | 2 | elbow/silhouette plot | 250 |
| 1.6 Hierarchical | four linkages (as taught), dendrogram, Ward cut | 2 | dendrogram | 200 |
| 1.7 DBSCAN | k-distance for eps, min_samples, noise | 2 | k-distance plot | 200 |
| 1.8 Comparison and model choice | silhouette, Davies-Bouldin, Calinski-Harabasz, stability (ARI), interpretability | 3 | comparison table/chart | 200 |
| 1.9 Cluster profiles | business personas | 1,3 | profile table, PCA scatter | 150 |
| **Task 2 Executive report** | | | | **1000** |
| 2.1 Executive summary | headline | 3 | - | 100 |
| 2.2 Method suitability | features + decisions in plain English | 3 | - | 200 |
| 2.3 Model comparison | strengths/limits | 3 | one chart | 250 |
| 2.4 Final model justification | technical + business | 3 | - | 150 |
| 2.5 Findings and recommendations | segment actions, ordered evidence → action | 3 | segment visual | 250 |
| 2.6 Limitations and next steps | specific | 3 | - | 50 |
| References | Harvard | - | - | excluded |
| Appendix A | Notebook code (readable) + optional GitHub link | - | - | excluded |

## Technical plan (proposal)

- Environment: Jupyter notebook, runnable locally (project `.venv`) and on Colab; seeds fixed; data path relative.
- Libraries: pandas, numpy, scikit-learn, scipy, matplotlib, seaborn.
- Candidate numeric features: `log_price`, `log_sold`, `available_clean` (+ censoring flag), `days_since_update`; categorical: normalised `category`, brand tier / branded flag, `is_us` location. Final set justified in 1.3.
- Validation: internal indices + stability across seeds/bootstrap; sensitivity with and without extreme sellers.

## Open questions

| Question | Why it matters | Owner | Status |
|---|---|---|---|
| Marking matrix from iLearn | Top-band wording for evidence matrix | Student | Closed 2026-10-24 |
| Deadline | Planning | Student | Closed (~2026-11-17) |
| Word-count convention | Budget | Student | Closed: body prose only; captions, tables, refs, appendix code excluded |
| Code appendix | Readability | Student | Closed: GitHub repo + Pages review HTML; appendix keeps code listing/link per brief |
| Assessed run environment | Screenshot evidence | Student | Closed: Google Colab |
| Visual palette | Consistency | Student | Closed: Arden Midnight/Tiffany |
| Brief + lesson PDFs in repo | Arden copyright notice | Student | Open: keep repo private (as COM7021) |

## Approval

- Student confirmed scope: tutor-feedback structure applied 2026-10-27 (ROC not required, confirmed by tutor)
- Student confirmed structure: pending review of `COM7022_Portfolio_25199053_final.docx`
- Date: 2026-10-27

## Handoff: remaining work (updated 2026-10-27, end of session)

**Standing rules from the student:** (1) the Colab notebook is the only home of analysis code, no new standalone scripts or files without asking; (2) the report file is built separately; (3) random seed is always **274**; (4) final deliverable to the tutor is **one Google Docs file** (no Drive connector in the Claude session, so it goes via a `.docx` the student uploads); (5) ROC is not required (tutor confirmed).

**State of the repo:** report (Word, PDF) and portal build cleanly from `_brain/REPORT.md` with the single script `scripts/build_report.py`; the notebook has 85 cells and was executed locally (seed 274, Carlito available) after its last edit; the report is about 3,900 words (Task 1: 2,394, Task 2: 1,518); PR #5 is open.

| # | Task | Status | Notes |
|---|---|---|---|
| 5 | Consolidate code into the Colab notebook | **Done** | Notebook is the only home of analysis code (diagrams in section 13); `scripts/build_report.py` is the only script (screenshots, Word/PDF, portal); output verified identical to the previous build. |
| 4 | Seed 274 everywhere | **Done locally; Colab re-run pending** | Notebook re-executed with seed 274, labels made canonical, every number re-verified (D18). Left: re-run on Colab with seed 274 and save to GitHub, then restore the 'also executed on Colab' sentence in Appendix A. |
| 7 | Rewrite the critical evaluation (section 7) | **Done, awaiting the student's review** | Rewritten around six arguments (see D19); two new notebook analyses (section 13: rule check and surrogate tree; revenue proxy and stock-ceiling share in the profile table). Report is now about 3,900 words; Task 2 is 1,518. The student may want to cut or push back on individual arguments. |
| 1 | Install Carlito font in the notebook | **Done locally; needs the Colab run (task 9) to confirm** | Guarded `ensure_carlito()` at the top of the style cell: installs `fonts-crosextra-carlito` when missing, registers it with matplotlib, falls back to DejaVu Sans if that fails. Verified here: command syntax and the register-after-install logic. In Colab, check the printed line says `Carlito font: available`. |
| 9 | Re-run the notebook on Colab with seed 274 and save to GitHub | Pending (after 1) | The Colab copy on main still holds seed-42 outputs. Check printed numbers against the report (K-Means silhouette 0.307, DBI 1.013, stability 0.929 ± 0.033, seed-to-seed ARI 0.964, best-sellers 90.7% of units, TabClustPFN auto k = 2 on 30/30 subsamples), save a copy to GitHub, restore the 'also executed on Colab' sentence in Appendix A, rebuild. |
| 3 | Raise the visual design to a much higher graphic level | Pending | Agree direction first (palette, chart types, what "standout" means), prototype 2-3 key figures, then roll out; keep colour-blind-safe and greyscale-readable. |
| 2 | Review visuals with the student | Pending | Also: the `colab-run-oct27` folder is not in the repo; ask where it is. |
| 6 | Google Docs version for the tutor | Pending (last) | Replace the static-page-number contents page with a real TOC field or linked headings; test the import; decide whether the 55-screenshot code appendix stays inside or is linked; share with Commenter access. |
| 8 | Email the tutor the Google Docs link and ask for feedback | Pending (after 6) | Text draft only (no Gmail draft, nothing sent); the student sends it. Draft below. Mention the student's own extras: HDBSCAN and TabClustPFN (and what the stock-censoring finding shows), the Colab run that reproduced every number, stability and sensitivity testing, the e-commerce model-fit analysis, the print-ready visuals. Needs: tutor name and email, language and tone, the Docs link with Commenter access. |

**Suggested order:** the Colab re-run (task 9, which also confirms task 1), then 3 and 2 together, then 6, then 8 (tasks 5, 4 and 7 are done).

## Open decisions and on-hold items (noted 2026-10-27, work paused at this stage by the student)

**On hold:** no further changes until the student decides. The student asked only to note what must be decided and that visuals and text must be brought into line.

**Principle:** every figure and table must agree with the sentences that cite it. Where they disagree, decide per case; the student's preference is to fix the text and caption first, and change a figure only if that is clearly better. Tracked as the audit task below.

| # | Decision or item | Options / state |
|---|---|---|
| D-1 | Figure 12 and the comparison paragraph (section 4.7) | The figure has six bars but the text compares three. A new paragraph and caption that walk through the figure were committed on branch `claude/determined-planck-oj1z8y` (no PR yet): **A** keep, **B** revert, **C** rewrite in the student's words. |
| D-2 | Change Figure 12 itself? | Option: group the bars (four segments, every listing covered: K-Means, Ward, TabClustPFN k = 4; not directly comparable: DBSCAN, HDBSCAN, TabClustPFN auto) and show k under each label. Not done; only if the student wants it. |
| D-3 | Notebook text | The "Reading the comparison" bullets in the notebook say the same as the old report text. Align after the Colab save, to avoid overwriting it. |
| D-4 | Colab run | Student ran it; a screenshot of the comparison figure matched the local numbers exactly. Still to confirm: that the copy was saved to GitHub, and that `Carlito font: available` was printed. Then restore the "also executed on Colab" sentence in Appendix A. |
| D-5 | Report length | About 3,970 words of body text against the 3,000-word guide; the student accepts some overshoot. Decide whether to trim, and what (candidate: section 7.5). |
| D-6 | Visual direction (tasks 3 and 2) | Mood (magazine-minimal, dashboard-energetic or classic academic), the two or three most important figures to prototype first, and whether the Midnight/Tiffany palette stays fixed. |
| D-7 | Tutor email | Text draft only, below; needs the tutor's name, language and tone, and the Docs link. |

**Audit task (session list #10):** go through each figure and table, list the claims the text makes about it, check each is visible, then fix text, caption or figure.

## Draft email to the tutor (text only, to finalise after the Google Docs link exists)

Conditional lines: the reproducibility sentence is true only after the Colab re-run with seed 274 (task 9); the word-count remark must match the final length.

> **Subject:** COM7022 portfolio draft for feedback (Student ID 25199053)
>
> Dear [Tutor name],
>
> I have shared my draft portfolio for COM7022 as a Google Doc, with comment access, so you can leave feedback directly on the text: [Google Docs link]
>
> It covers both tasks on the e-commerce fragrance dataset: data preparation, clustering with K-Means, Ward hierarchical clustering and DBSCAN, PCA, evaluation with several metrics, and an executive report with recommendations. All code is in one Colab notebook, linked from the document together with every figure, table and code screenshot.
>
> Beyond the brief, I added:
> - **Two newer models**, HDBSCAN and the TabClustPFN tabular foundation model (2026), compared against the classical methods. Both showed that the platform's stock figure is capped at 10 units, and that this affects what algorithms find.
> - **A reproducibility check:** I ran the notebook on Colab as well as locally with a fixed seed (274), and every reported number matched.
> - **Stability and sensitivity tests** (resampling, seeds, scaling, outlier removal), because a cluster solution is only as good as its robustness.
> - **A model-fit analysis for e-commerce** (coverage, scoring new listings, scalability, explainability) alongside the metrics.
> - **A critical evaluation** that asks what the segmentation adds beyond a sales ranking, and turns each recommendation into a testable hypothesis.
>
> I would especially value your feedback on:
> 1. Whether the critical evaluation in Task 2 is convincing and well argued.
> 2. Whether the structure and length suit the 3,000-word brief (the body is currently about 3,900 words, and I can trim).
> 3. Whether the recommendations are practical for a non-technical audience.
>
> Thank you for your time.
>
> Kind regards,
> [Your name]
> Student ID 25199053
