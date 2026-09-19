# papers/

Local copies of the sources the wiki is extracted from. **Gitignored** except
this file: the copies are not ours to redistribute, and the canonical pointer
is the URL in each source card under `wiki/sources/`.

## Layout

One directory per paper, `<firstauthor>-<year>-<slug>/`, holding the HTML page
plus its page requisites (images, CSS) with links rewritten to local paths.
Prefer arXiv's own HTML rendering (`arxiv.org/html/<id>`); fall back to
`ar5iv.labs.arxiv.org/html/<id>` if arXiv has none, then to the PDF.

The three R0 papers predate this layout and sit as browser-saved single HTML
files in the directory root; their images are not all local.

## Re-downloading

```sh
dl() { dir="$1"; url="$2"; shift 2; mkdir -p "papers/$dir"
  wget -e robots=off --timeout=30 --tries=2 -U 'Mozilla/5.0' \
       -p -k -E -nH --cut-dirs=1 -P "papers/$dir" "$@" "$url"; }

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

Downloaded 2026-09-19. Titles were checked against the reading list after
download; every `<img>` in the four arXiv pages resolves to a local file.
