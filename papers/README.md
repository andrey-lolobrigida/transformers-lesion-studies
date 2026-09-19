# papers/

Local copies of the sources the wiki is extracted from. **Gitignored** except
this file: the copies are not ours to redistribute, and the canonical pointer
is the URL in each source card under `wiki/sources/`.

## Layout

One directory per paper, `<firstauthor>-<year>-<slug>/`, holding the HTML page
plus its page requisites (images, CSS) with links rewritten to local paths.
Prefer arXiv's own HTML rendering (`arxiv.org/html/<id>`); fall back to
`ar5iv.labs.arxiv.org/html/<id>` if arXiv has none, then to the PDF.

The two Transformer Circuits Thread pages embed every figure as a base64 data
URI, so they arrive as a single self-contained HTML file. Distill's Zoom In
references seven images that `wget -p` does not pick up; they are fetched
explicitly below.

## Re-downloading

```sh
dl() { dir="$1"; url="$2"; shift 2; mkdir -p "papers/$dir"
  wget -e robots=off --timeout=30 --tries=2 -U 'Mozilla/5.0' \
       -p -k -E -nH --cut-dirs=1 -P "papers/$dir" "$@" "$url"; }

# R0
dl olah-2020-zoom-in            https://distill.pub/2020/circuits/zoom-in/ -H -D distill.pub
( cd papers/olah-2020-zoom-in/circuits/zoom-in && for i in curve-orientations-a \
    curve-orientations-b dog-circuit-2 oriented-dog-heads dog-merge car-circuit \
    superposition; do wget -q -U 'Mozilla/5.0' -O "images/$i.png" \
    "https://distill.pub/2020/circuits/zoom-in/images/$i.png"; done )
dl elhage-2021-framework        https://transformer-circuits.pub/2021/framework/index.html -H -D transformer-circuits.pub
dl olsson-2022-induction-heads  https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html -H -D transformer-circuits.pub

# R1 — required
dl wang-2022-ioi                  https://arxiv.org/html/2211.00593
dl miller-2024-faithfulness       https://arxiv.org/html/2407.08734
# R1 — skim / conditional
dl meng-2022-rome                 https://arxiv.org/html/2202.05262
dl makelov-2023-subspace-illusion https://arxiv.org/html/2311.17030
dl chan-2022-causal-scrubbing \
   "https://www.alignmentforum.org/posts/JvZhhzycHu2Yd57RN/causal-scrubbing-a-method-for-rigorously-testing" \
   -H -D alignmentforum.org,res.cloudinary.com,lesswrong.com
```

All eight downloaded 2026-09-19. Titles were checked against the reading list
after download; every `<img>` in every page resolves to a local file or is an
embedded data URI.
