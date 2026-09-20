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

    @property
    def prompt(self) -> str:
        """The model input: ``text`` with the trailing answer removed. The
        released code keeps the answer in the text and reads the logits at
        the position before it (its ``end`` index); this is the same thing."""
        suffix = " " + self.io
        assert self.text.endswith(suffix), self
        return self.text[: -len(suffix)]


def generate_prompts(n: int, seed: int, orders: tuple[str, ...] = ("BABA", "ABBA")) -> list[IOIPrompt]:
    """Draw ``n`` prompts from p_IOI with a private RNG seeded by ``seed``."""
    rng = random.Random(seed)
    templates = [(order, i, t) for order in orders for i, t in enumerate(ORDERS[order])]
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
        out.append(IOIPrompt(text=text, io=name_1, s=name_2, template_idx=idx, order=order))
    return out
