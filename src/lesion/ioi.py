"""IOI prompt generation for the `p_IOI` distribution of Wang et al. 2022.

Ported from the paper's released code (``redwoodresearch/Easy-Transformer``,
``easy_transformer/ioi_dataset.py``, commit ``e168301``, 2022-11-18), which is
the only version of that file in the repository's history. The templates match
the paper's Appendix E (Fig. 14) exactly.

Known discrepancies with the paper text, unresolved: the paper says "100
English first names" and that places and objects were "chosen among a hand-made
list of 20 common words" [wang-2022 App. E]; the released code has 99 distinct
names and 8 places and 8 objects. This module uses the released lists verbatim.
The paper-era lists are not recoverable from the repository, whose history
starts (2022-11-18) after v1 of the paper (2022-11-01).

Sampling follows ``gen_prompt_uniform`` in the released code: template uniform
over the chosen order(s); three names drawn with replacement until distinct
(the third is unused for IOI but is drawn, so the random stream matches); one
place and one object uniform. No ``symmetric`` pairing, no prefixes.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from src.lesion.battery import AlignmentError, Corruption, PromptPair, encode, resolve_scheme, with_bos

NAMES = [
    "Michael", "Christopher", "Jessica", "Matthew", "Ashley", "Jennifer",
    "Joshua", "Amanda", "Daniel", "David", "James", "Robert", "John", "Joseph",
    "Andrew", "Ryan", "Brandon", "Jason", "Justin", "Sarah", "William",
    "Jonathan", "Stephanie", "Brian", "Nicole", "Nicholas", "Anthony",
    "Heather", "Eric", "Elizabeth", "Adam", "Megan", "Melissa", "Kevin",
    "Steven", "Thomas", "Timothy", "Christina", "Kyle", "Rachel", "Laura",
    "Lauren", "Amber", "Brittany", "Danielle", "Richard", "Kimberly",
    "Jeffrey", "Amy", "Crystal", "Michelle", "Tiffany", "Jeremy", "Benjamin",
    "Mark", "Emily", "Aaron", "Charles", "Rebecca", "Jacob", "Stephen",
    "Patrick", "Sean", "Erin", "Jamie", "Kelly", "Samantha", "Nathan", "Sara",
    "Dustin", "Paul", "Angela", "Tyler", "Scott", "Katherine", "Andrea",
    "Gregory", "Erica", "Mary", "Travis", "Lisa", "Kenneth", "Bryan",
    "Lindsey", "Kristen", "Jose", "Alexander", "Jesse", "Katie", "Lindsay",
    "Shannon", "Vanessa", "Courtney", "Christine", "Alicia", "Cody",
    "Allison", "Bradley", "Samuel",
]

PLACES = ["store", "garden", "restaurant", "school", "hospital", "office", "house", "station"]
OBJECTS = ["ring", "kiss", "bone", "basketball", "computer", "necklace", "drink", "snack"]

# Fig. 14 of the paper, verbatim. [B] is the subject (S), [A] the indirect
# object (IO). In this order the first clause reads "[B] and [A]" — BABA.
BABA_TEMPLATES = [
    "Then, [B] and [A] went to the [PLACE]. [B] gave a [OBJECT] to [A]",
    "Then, [B] and [A] had a lot of fun at the [PLACE]. [B] gave a [OBJECT] to [A]",
    "Then, [B] and [A] were working at the [PLACE]. [B] decided to give a [OBJECT] to [A]",
    "Then, [B] and [A] were thinking about going to the [PLACE]. [B] wanted to give a [OBJECT] to [A]",
    "Then, [B] and [A] had a long argument, and afterwards [B] said to [A]",
    "After [B] and [A] went to the [PLACE], [B] gave a [OBJECT] to [A]",
    "When [B] and [A] got a [OBJECT] at the [PLACE], [B] decided to give it to [A]",
    "When [B] and [A] got a [OBJECT] at the [PLACE], [B] decided to give the [OBJECT] to [A]",
    "While [B] and [A] were working at the [PLACE], [B] gave a [OBJECT] to [A]",
    "While [B] and [A] were commuting to the [PLACE], [B] gave a [OBJECT] to [A]",
    "After the lunch, [B] and [A] went to the [PLACE]. [B] gave a [OBJECT] to [A]",
    "Afterwards, [B] and [A] went to the [PLACE]. [B] gave a [OBJECT] to [A]",
    "Then, [B] and [A] had a long argument. Afterwards [B] said to [A]",
    "The [PLACE] [B] and [A] went to had a [OBJECT]. [B] gave it to [A]",
    "Friends [B] and [A] found a [OBJECT] at the [PLACE]. [B] gave it to [A]",
]


def _to_abba(template: str) -> str:
    """Swap the first [B] and the first [A] (the first clause), as the paper
    describes and the released code does."""
    b = template.index("[B]")
    a = template.index("[A]")
    assert b < a, template
    return template[:b] + "[A]" + template[b + 3 : a] + "[B]" + template[a + 3 :]


ABBA_TEMPLATES = [_to_abba(t) for t in BABA_TEMPLATES]

ORDERS = {"BABA": BABA_TEMPLATES, "ABBA": ABBA_TEMPLATES}


@dataclass(frozen=True)
class IOIPrompt:
    text: str  # the full sentence as the released code stores it, answer included
    io: str  # the correct next token, without leading space
    s: str  # the repeated (subject) name
    template_idx: int
    order: str  # "BABA" or "ABBA"
    place: str  # drawn even when the template has no [PLACE]; keeps the stream identical
    obj: str  # likewise for [OBJECT]

    @property
    def prompt(self) -> str:
        """The model input: ``text`` with the trailing answer removed. The
        released code keeps the answer in the text and reads the logits at
        the position before it (its ``end`` index); this is the same thing."""
        suffix = " " + self.io
        assert self.text.endswith(suffix), self
        return self.text[: -len(suffix)]


def generate_prompts(n: int, seed: int, orders: tuple[str, ...] = ("BABA", "ABBA"),
                     templates_per_order: int = 15) -> list[IOIPrompt]:
    """Draw ``n`` prompts from p_IOI with a private RNG seeded by ``seed``.
    ``templates_per_order`` < 15 keeps templates 0..k-1 of each order: the
    released code's ``mixed`` mode with its default count uses 7 (O-014), one
    of E2's bracket corners (D-015 item 5). At 15 the stream is the one every
    earlier artifact used."""
    if not 1 <= templates_per_order <= len(BABA_TEMPLATES):
        raise ValueError(f"templates_per_order must be in 1..{len(BABA_TEMPLATES)}, got {templates_per_order}")
    rng = random.Random(seed)
    templates = [(order, i, t) for order in orders for i, t in enumerate(ORDERS[order]) if i < templates_per_order]
    out: list[IOIPrompt] = []
    for _ in range(n):
        order, idx, template = rng.choice(templates)
        name_1 = name_2 = name_3 = ""
        while len({name_1, name_2, name_3}) < 3:
            name_1 = rng.choice(NAMES)
            name_2 = rng.choice(NAMES)
            name_3 = rng.choice(NAMES)
        place = rng.choice(PLACES)
        obj = rng.choice(OBJECTS)
        text = template.replace("[PLACE]", place).replace("[OBJECT]", obj)
        text = text.replace("[A]", name_1).replace("[B]", name_2)
        out.append(IOIPrompt(text=text, io=name_1, s=name_2, template_idx=idx, order=order, place=place, obj=obj))
    return out


# Position labels, Wang et al.'s names: IO and S1 are the two names of the
# first clause, S1+1 the token after S1, S2 the repeated name in the second
# clause, END the last prompt token (whose logits are read).
LABELS = ("IO", "S1", "S1+1", "S2", "END")

P_ABC = Corruption(
    name="p_ABC",
    removes="the repetition of the subject name: no name occurs twice, so nothing in the prompt "
            "singles out an indirect object",
    inserts="three distinct fresh names in the three name slots, none equal to the clean IO or S; "
            "same template, place and object",
    source="wang-2022 §2.1",
)

# Wang et al. App. A: three transformations of p_IOI, composed into five
# counterparts that separate the position signal (where the repeated name
# sits) from the token signal (which name is repeated). Each entry fills the
# three name slots (S1 slot, IO slot, S2 slot) with a symbol: IO and S are the
# clean names, IO' and S' two random names distinct from each other and from
# IO and S. The symbol at the S2 slot is always the repeated one.
APP_A = {
    "rand_names": ("S'", "IO'", "S'"),  # random name flip
    "flip": ("IO", "S", "S"),  # IO <-> S1 flip
    "flip_rand": ("IO'", "S'", "S'"),  # random name flip, then IO <-> S1 flip
    "repl_flip": ("IO", "S", "IO"),  # IO <- S2 replacement, then IO <-> S1 flip
    "repl": ("S", "IO", "IO"),  # IO <- S2 replacement
}

_APP_A_SOURCE = "wang-2022 App. A"
SCHEMES = {
    "p_ABC": P_ABC,
    "rand_names": Corruption(
        name="rand_names",
        removes="the token signal: IO and S no longer occur, so neither answer token is in the prompt "
                "(token signal uncorrelated); the position signal is kept",
        inserts="two fresh distinct names, each substituted consistently for IO and for S at every "
                "occurrence; the repeated name stays at the S1 and S2 positions; template, place and object kept",
        source=_APP_A_SOURCE),
    "flip": Corruption(
        name="flip",
        removes="the position signal: IO and S1 exchange positions, so the repeated name now occupies the "
                "IO and S2 positions (position signal inverted); the token signal is kept (S repeated, IO once)",
        inserts="the same two clean names with IO and S1 swapped; template, place and object kept",
        source=_APP_A_SOURCE),
    "flip_rand": Corruption(
        name="flip_rand",
        removes="both signals: fresh names replace IO and S (token signal uncorrelated) and the repeated name "
                "occupies the IO and S2 positions (position signal inverted)",
        inserts="two fresh distinct names, then IO and S1 exchanged; template, place and object kept",
        source=_APP_A_SOURCE),
    "repl_flip": Corruption(
        name="repl_flip",
        removes="the token signal, inverted: IO is now the repeated name and S occurs once; the repeated name "
                "stays at the S1 and S2 positions (position signal original)",
        inserts="IO at the S1 and S2 positions, S at the IO position (S2 replaced by IO, then IO and S1 "
                "exchanged); template, place and object kept",
        source=_APP_A_SOURCE),
    "repl": Corruption(
        name="repl",
        removes="both signals, inverted: S2 is replaced by IO, so IO is repeated (token signal inverted) at the "
                "IO and S2 positions (position signal inverted), and S occurs once, at S1",
        inserts="the IO name at the S2 position; template, place and object kept",
        source=_APP_A_SOURCE),
}


def app_a_counterpart(p: IOIPrompt, scheme: str, rng: random.Random) -> tuple[str, str, str]:
    """The App. A counterpart of ``p`` [wang-2022 App. A], built from the
    template like ``abc_counterpart``. Returns (prompt text without the answer,
    the name that occurs once, the name that occurs twice). Two random names
    are drawn for every scheme so the stream does not depend on which scheme
    uses them."""
    template = ORDERS[p.order][p.template_idx]
    assert template.endswith(" [A]"), template
    body = template[: -len(" [A]")]
    io_r, s_r = rng.sample([nm for nm in NAMES if nm not in (p.io, p.s)], 2)
    names = {"IO": p.io, "S": p.s, "IO'": io_r, "S'": s_r}
    s1_sym, io_sym, s2_sym = APP_A[scheme]
    body = body.replace("[PLACE]", p.place).replace("[OBJECT]", p.obj)
    text = body.replace("[A]", names[io_sym]).replace("[B]", names[s1_sym], 1).replace("[B]", names[s2_sym], 1)
    once_sym = io_sym if s1_sym == s2_sym else s1_sym
    return text, names[once_sym], names[s2_sym]


def abc_counterpart(p: IOIPrompt, rng: random.Random) -> str:
    """The p_ABC prompt paired with ``p``: same template, place and object;
    the three name slots filled with three distinct names drawn from NAMES
    minus {p.io, p.s}; the answer slot removed [wang-2022 §2.1]. Uses its own
    RNG so the clean stream of ``generate_prompts`` is untouched."""
    template = ORDERS[p.order][p.template_idx]
    assert template.endswith(" [A]"), template
    body = template[: -len(" [A]")]
    assert body.count("[A]") == 1 and body.count("[B]") == 2, body
    a, b1, b2 = rng.sample([nm for nm in NAMES if nm not in (p.io, p.s)], 3)
    body = body.replace("[PLACE]", p.place).replace("[OBJECT]", p.obj)
    return body.replace("[A]", a).replace("[B]", b1, 1).replace("[B]", b2, 1)


def name_positions(ids: list[int], io_id: int, s_id: int) -> dict[str, int]:
    """Label indices from the clean token ids. S must occur exactly twice and
    IO exactly once; anything else is a misalignment."""
    s_idx = [i for i, t in enumerate(ids) if t == s_id]
    io_idx = [i for i, t in enumerate(ids) if t == io_id]
    if len(s_idx) != 2 or len(io_idx) != 1:
        raise AlignmentError(f"expected S twice and IO once, got S at {s_idx}, IO at {io_idx}")
    return {"IO": io_idx[0], "S1": s_idx[0], "S1+1": s_idx[0] + 1, "S2": s_idx[1], "END": len(ids) - 1}


class IOIBattery:
    """Clean p_IOI paired with p_ABC (default) or one of Wang's App. A counterparts. Implements ``battery.Battery``."""

    name = "ioi"
    labels = LABELS
    schemes = ("p_ABC", "rand_names", "flip", "flip_rand", "repl_flip", "repl")
    expected_direction = "positive"
    default_prepend_bos = False  # E0 and E1a ran without BOS: the paper's procedure
    template_set = "wang-2022 App. E Fig. 14: 15 BABA + 15 ABBA templates, released word lists (99 names, 8 places, 8 objects)"

    def __init__(self, tokenizer, scheme: str | None = None, templates_per_order: int = 15) -> None:
        self.tok = tokenizer
        self.scheme = resolve_scheme(self.schemes, scheme)
        self.corruption = SCHEMES[self.scheme]
        if not 1 <= templates_per_order <= len(BABA_TEMPLATES):
            raise ValueError(f"templates_per_order must be in 1..{len(BABA_TEMPLATES)}, got {templates_per_order}")
        self.templates_per_order = templates_per_order
        if templates_per_order != len(BABA_TEMPLATES):  # E2 bracket corner; the default string is unchanged
            self.template_set = (f"{IOIBattery.template_set}; subset: templates 0-{templates_per_order - 1} of each "
                                 f"order ({2 * templates_per_order} templates), the released code's `mixed` "
                                 f"default (O-014)")

    def encode_clean(self, p: IOIPrompt, prepend_bos: bool) -> tuple[list[int], int, int, dict[str, int]]:
        """E0's encoder: (ids, IO id, S id, positions), every alignment the
        paper relies on asserted."""
        ids = encode(self.tok, p.prompt)
        io = encode(self.tok, " " + p.io)
        s = encode(self.tok, " " + p.s)
        if len(io) != 1 or len(s) != 1:
            raise AlignmentError(f"name is not a single token: {p.io!r} -> {io}, {p.s!r} -> {s}")
        if ids + io != encode(self.tok, p.text):
            raise AlignmentError(f"tokenisation of prompt + answer differs from the full sentence: {p.text!r}")
        positions = name_positions(ids, io[0], s[0])
        if prepend_bos:
            ids, positions = with_bos(ids, positions, self.tok.bos_token_id)
        return ids, io[0], s[0], positions

    def encode_pair(self, p: IOIPrompt, corrupt_text: str, prepend_bos: bool) -> PromptPair:
        ids, io, s, pos = self.encode_clean(p, prepend_bos)
        cids = encode(self.tok, corrupt_text)
        if prepend_bos:
            cids = [self.tok.bos_token_id, *cids]
        if len(cids) != len(ids):
            raise AlignmentError(f"p_ABC length {len(cids)} != p_IOI length {len(ids)}: {corrupt_text!r}")
        slots = {pos["IO"], pos["S1"], pos["S2"]}
        new = {cids[i] for i in slots}
        if len(new) != 3 or new & {io, s}:
            raise AlignmentError(f"p_ABC names not three fresh distinct tokens: {corrupt_text!r}")
        for i, (c, k) in enumerate(zip(ids, cids)):
            if (c != k) != (i in slots):
                raise AlignmentError(f"p_ABC differs from p_IOI outside the name slots at {i}: {corrupt_text!r}")
        return PromptPair(
            clean_ids=tuple(ids), corrupt_ids=tuple(cids), answer_id=io, competitor_id=s,
            positions=pos, corrupt_positions=dict(pos), template=f"{p.order}/{p.template_idx}",
            meta={"order": p.order, "template_idx": str(p.template_idx), "io": p.io, "s": p.s,
                  "clean_text": p.prompt, "corrupt_text": corrupt_text},
        )

    def encode_app_a_pair(self, p: IOIPrompt, corrupt_text: str, once: str, repeated: str,
                          prepend_bos: bool) -> PromptPair:
        """An App. A pair. Outside the three name slots the corrupt prompt must
        equal the clean one. Corrupt labels are the roles in the corrupt
        sentence (IO = the name occurring once, S1/S2 = the repeated name), so
        they move when the scheme moves names."""
        ids, io, s, pos = self.encode_clean(p, prepend_bos=False)
        cids = encode(self.tok, corrupt_text)
        if len(cids) != len(ids):
            raise AlignmentError(f"{self.scheme} length {len(cids)} != p_IOI length {len(ids)}: {corrupt_text!r}")
        slots = {pos["IO"], pos["S1"], pos["S2"]}
        for i, (c, k) in enumerate(zip(ids, cids)):
            if i not in slots and c != k:
                raise AlignmentError(f"{self.scheme} differs from p_IOI outside the name slots at {i}: {corrupt_text!r}")
        once_ids, rep_ids = encode(self.tok, " " + once), encode(self.tok, " " + repeated)
        if len(once_ids) != 1 or len(rep_ids) != 1:
            raise AlignmentError(f"name is not a single token: {once!r} -> {once_ids}, {repeated!r} -> {rep_ids}")
        cpos = name_positions(cids, once_ids[0], rep_ids[0])
        if prepend_bos:
            ids, pos = with_bos(ids, pos, self.tok.bos_token_id)
            cids, cpos = with_bos(cids, cpos, self.tok.bos_token_id)
        return PromptPair(
            clean_ids=tuple(ids), corrupt_ids=tuple(cids), answer_id=io, competitor_id=s,
            positions=pos, corrupt_positions=cpos, template=f"{p.order}/{p.template_idx}",
            meta={"order": p.order, "template_idx": str(p.template_idx), "io": p.io, "s": p.s,
                  "clean_text": p.prompt, "corrupt_text": corrupt_text},
        )

    def pairs(self, n: int, seed: int, prepend_bos: bool) -> list[PromptPair]:
        prompts = generate_prompts(n, seed, templates_per_order=self.templates_per_order)
        if self.scheme == "p_ABC":  # E1a's path, byte for byte
            rng = random.Random(f"p_ABC/{seed}")
            return [self.encode_pair(p, abc_counterpart(p, rng), prepend_bos) for p in prompts]
        rng = random.Random(f"{self.scheme}/{seed}")
        return [self.encode_app_a_pair(p, *app_a_counterpart(p, self.scheme, rng), prepend_bos) for p in prompts]
