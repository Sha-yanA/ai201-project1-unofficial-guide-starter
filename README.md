# The Unofficial Guide — Project 1

<!-- > **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit. -->

<!-- --- -->

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

UF campus dining experiences: student opinions and first-hand accounts about dining halls, the Reitz Union food court, meal plans, and eating on campus at the University of Florida. Students making decisions about meal plans, where to eat between classes, or how to handle dietary restrictions can't get honest answers from official sources. UF's own dining pages tell you what locations exist and what things cost, not what's actually good or worth avoiding. The real student consensus is scattered across Yelp, Reddit, Niche, Spoon University, and the Alligator, with no single place that pulls it together into something searchable and answerable.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| #  | Source           | Description                   | URL or Location |
|----|------------------|-------------------------------|-----------------|
| 1  | Yelp             | Student reviews of Broward dining hall | `https://www.yelp.com/biz/fresh-food-company-broward-dining-gainesville` |
| 2  | Restaurantji     | Aggregated student reviews of Gator Corner | `https://www.restaurantji.com/fl/gainesville/gator-corner-dining-center-/` |
| 3  | Spoon University | Student-written review of Cravings Campus Kitchen (2023) | `https://spoonuniversity.com/school/ufl/reviewing-the-new-dining-hall/`           |
| 4  | The Alligator    | Student reactions to renovated Broward reopening (Aug 2024) | `https://www.alligator.org/article/2024/08/the-eatery-at-broward-hall-first-look`|
| 5  | The Alligator    | Student opinions on the tent dining hall during Broward closure (Jan 2024) | `https://www.alligator.org/article/2024/01/broward-tent` |
| 6  | The Alligator    | Students on vegan and dietary restriction options on campus (Jan 2024) | `https://www.alligator.org/article/2024/01/uf-vegan-experience`       |
| 7  | The Alligator    | Student dissatisfaction with on-campus dining, off-campus alternatives (Sep 2024) | `https://www.alligator.org/article/2024/09/what-to-know-about-a-new-student-meal-plan-alternative` |
| 8  | Niche            | Aggregated student reviews covering campus dining | `https://www.niche.com/colleges/university-of-florida/campus-life/` |
| 9  | Wanderlog        | Student reviews of the Reitz Union food court | `https://wanderlog.com/place/details/11039454/reitz-union` |
| 10 | Reddit r/ufl     | Student thread on campus dining | `https://www.reddit.com/r/ufl/comments/1szl19w/new_uf_meal_plans_breakdown/` |
| 11 | Reddit r/ufl     | Student thread for food budgeting | `https://www.reddit.com/r/ufl/comments/q4af5g/how_much_money_do_you_spend_on_food/` |
| 12 | Reddit r/ufl     | Student thread  covering  late-night dining| `https://www.reddit.com/r/ufl/comments/jh2ikl/good_food_after_midnight/` |
---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 400–500 characters (roughly 100–125 tokens)

**Overlap:** 50 characters. Small because review documents are opinion units with no cross-boundary dependencies; overlap mainly helps when splitting long Alligator article paragraphs

**Why these choices fit your documents:** The corpus is dominated by individual review snippets where the meaningful unit is one person's complete verdict on one location. Splitting mid-review destroys the location+opinion pairing retrieval depends on. 400–500 chars preserves most reviews as whole chunks while staying well under all-MiniLM-L6-v2's 256-token ceiling. Overlap is intentionally small because review documents have no cross-boundary dependencies; it only helps when splitting longer Alligator article paragraphs. Split order: review/comment boundaries first, then paragraph breaks (Alligator, Spoon University), then character limit with overlap as a fallback for long prose (Reddit meal plan post).

**Final chunk count:** 332 (max 500 chars, avg 224 chars)

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`, running locally. Produces 384-dimensional vectors. Chosen because it requires no API key, has no rate limits, and its 256-token input ceiling comfortably covers our 500-character chunks (roughly 125 tokens).

**Production tradeoff reflection:** The main tradeoffs for a real deployment are context length, accuracy, and hosting cost. `all-MiniLM-L6-v2` caps at 256 tokens, which is fine for short reviews but would truncate longer documents in a different domain. OpenAI's `text-embedding-3-small` handles up to 8k tokens and scores higher on semantic benchmarks, but adds per-call API cost, latency, and an external dependency. A multilingual model like `multilingual-e5-large` would handle non-English content (a few reviews in this corpus are in Chinese) but is significantly larger and slower to run locally. For this project the local, zero-cost model is the right tradeoff; in production I would move to an API-hosted model with longer context for better recall on complex queries.

---

## Retrieval Test Results

**Query 1: "Are there vegan options at UF dining halls?"**

| Rank | Source | Location | Distance | Chunk text (first 200 chars) |
|------|--------|----------|----------|------------------------------|
| 1 | The Alligator | UF Dining Halls (Vegan Options) | 0.2625 | *"I'm vegan by choice, but some people are for religious, cultural reasons," she said. "I feel like [dining halls] should really just be more easily accommodated..."* |
| 2 | The Alligator | UF Dining Halls (Vegan Options) | 0.2931 | *"All the other campus dining halls change the daily menu option once every four weeks, and there are both vegan entrees and plant-based substitutes available."* |
| 3 | The Alligator | UF Dining Halls (Vegan Options) | 0.3321 | *"I know a lot of [vegan students] are looking for more of an entree, not just the sides, so we're trying to get there and implement more vegan options," said Marc Cruz, the district executive chef.* |
| 4 | The Alligator | UF Dining Halls (Vegan Options) | 0.3381 | *"For vegan students like Maxine Sculthorpe, an 18-year-old UF biomedical engineering freshman, walking into a new dining hall can be intimidating because her food options are frequently limited..."* |
| 5 | Yelp | Broward Dining Hall | 0.3394 | *"...the vegan bar has some of the best food out due to being almost forced into using higher quality ingredients. Overall, it's not a great time, but..."* |

**Why these chunks are relevant:** The query contains the exact phrase "vegan options" and "dining halls," which appear verbatim in chunks 1–4. The embedding model maps "vegan" and "dining accommodations" tightly in vector space, so all five top hits come from the single Alligator article specifically about vegan students - exactly the right document. Chunk 5 (Yelp/Broward) surfaces because it mentions the vegan bar as a named physical feature of the dining hall. All distances are under 0.35, indicating strong semantic alignment with the query.

---

**Query 2: "What do students say about food quality at Gator Corner compared to Broward?"**

| Rank | Source | Location | Distance | Chunk text (first 200 chars) |
|------|--------|----------|----------|------------------------------|
| 1 | Restaurantji | Gator Corner Dining Center | 0.2816 | *"I can't say enough good things about Gator Corner! Every visit feels like a treat. The food options are abundant, catering to all tastes and dietary preferences, and everything is always fresh..."* |
| 2 | Yelp | Broward Dining Hall | 0.3370 | *"Just a quick update to my previous review since I recently ate here with a friend who is a student at UF. For what it is, which is college food, Broward is really good overall..."* |
| 3 | The Alligator | Norman Tent Dining (Broward Renovation) | 0.3411 | *"While Dinka describes the food as hit-or-miss — sometimes tasting better than the Broward fare she ate last semester, and sometimes tasting like 'slop'..."* |
| 4 | Yelp | Broward Dining Hall | 0.3613 | *"...the dessert station is slamming. The confections completely outperform that of Broward's vastly inferior, and barbaric cousin Gator D. Pretty good for cafeteria food."* |
| 5 | Yelp | Broward Dining Hall | 0.3782 | *"Now, Fresh Food Company at Broward is not fancy, not at all. This is college grub, but it's very good for what it is, and the staff is very friendly..."* |

**Why these chunks are relevant:** The query mentions both "Gator Corner" and "Broward" as named entities alongside the phrase "food quality." The embedding model retrieves chunks where both names co-occur or where one is contrasted with the other. Chunk 1 is the top Gator Corner review; chunks 2 and 5 are Broward reviews with explicit quality assessments. Chunk 4 is especially useful because it directly names both dining halls in the same sentence ("Broward's vastly inferior… cousin Gator D"), giving the LLM direct comparative material. Chunk 3 provides a student quote about Broward food being "hit-or-miss," which captures the divided opinion accurately.

---

**Query 3: "Where can UF students find food after midnight?"**

| Rank | Source | Location | Distance | Chunk text (first 200 chars) |
|------|--------|----------|----------|------------------------------|
| 1 | The Alligator | UF Dining / Bite Club | 0.3852 | *"UF's on-campus meal plans are abundantly used by students but lack one essential feature: off-campus dining."* |
| 2 | Reddit r/ufl | Gainesville Late-Night Dining | 0.3994 | *"Let me put you on to the late night options as I'm a night owl. You have Taco Bell on Archer which closes at like 3 am. I went the other night and it was closed around 2:30 but it usually closes at 3..."* |
| 3 | The Alligator | Norman Tent Dining (Broward Renovation) | 0.4132 | *"Norman offers three all-you-can-eat meal stations in addition to salad, cereal and dessert bars. Students can visit seven days per week from 7 a.m. to 9 p.m. on weekdays..."* |
| 4 | Restaurantji | Gator Corner Dining Center | 0.4274 | *"All you can eat restaurant that mostly serves UF students. The food is a hit or miss... The location always serves pizza, salad, coffee, waffles (waffle maker)..."* |
| 5 | Yelp | Broward Dining Hall | 0.4325 | *"The Fresh Food Company is located on the UF campus at the Broward Dining complex on Inner Drive. This makes the location handy for a number of dorms..."* |

---

## Example Responses

**Response 1 - "What food options are available at the Reitz Union?"**

> The Reitz Union has a variety of food options, including Mi Apa, Panda Express, Starbucks, Halal Shack, Baba's Pizza, Subway, and a market. Additionally, there are stations for making subs, a "Fresh Mex Burrito Bar", and a selection of desserts. Some reviewers also mention being able to grab a plate of prepared dishes, such as fish with yellow rice. Overall, there are many different restaurants and eateries to choose from at the Reitz Union.
>
> *(1_yelp_broward_dining.txt, 9_wanderlog_reitz_union.txt)*

Sources shown in the interface below the answer card:

| Type | Outlet | Location | Link |
|------|--------|----------|------|
| Review | Yelp | Broward Dining Hall | [View source ↗](https://www.yelp.com/biz/fresh-food-company-broward-dining-gainesville) |
| Review | Wanderlog | Reitz Union Food Court | [View source ↗](https://wanderlog.com/place/details/11039454/reitz-union) |

---

**Response 2 - "Are there vegan options at UF dining halls?"**

> Yes, there are vegan options available at UF dining halls. Both vegan entrees and plant-based substitutes can be found, although some students feel that the options are limited and not always satisfying. The district executive chef is working to implement more vegan options, particularly entrees, to better accommodate vegan students. Additionally, some dining halls have a vegan bar with high-quality ingredients, which can offer some of the best food options.
>
> *(6_alligator_uf_vegan.txt, 1_yelp_broward_dining.txt)*

Sources shown in the interface below the answer card:

| Type | Outlet | Location | Link |
|------|--------|----------|------|
| Article | The Alligator | UF Dining Halls (Vegan Options) | [View source ↗](https://www.alligator.org/article/2024/01/uf-vegan-experience) |
| Review | Yelp | Broward Dining Hall | [View source ↗](https://www.yelp.com/biz/fresh-food-company-broward-dining-gainesville) |

---

**Response 3 (out-of-scope) - "What is the best Italian restaurant in Gainesville?"**

> I don't have enough information in my sources to answer that.

The system returned the refusal because no retrieved chunk passed the cosine distance threshold of 0.70: the corpus contains no content about Italian restaurants in Gainesville, so no relevant context was surfaced and the LLM was never called. The UI renders this in a yellow warning card with the message above and a prompt to try a different question.

---

## Query Interface

**Input field**

A single multi-line text box labelled "Your question" with placeholder text *"e.g. Is the UF meal plan worth buying?"* The user types a free-form natural-language question and submits by pressing the "Ask" button or hitting Enter. Five pre-loaded example questions are shown below the input as one-click shortcuts.

**Output fields**

*Answer card* - an HTML panel rendered to the right of a blue left-border stripe. It shows the LLM's grounded prose answer (3–6 sentences). When the system cannot answer, it renders a yellow warning card instead. At the bottom of every successful answer, the filenames of the source documents are appended in parentheses (e.g., `(6_alligator_uf_vegan.txt, 1_yelp_broward_dining.txt)`), this attribution is programmatic, not generated by the LLM.

*Sources table* - a formatted HTML table below the answer card with one row per unique source. Each row shows a colour-coded document-type badge (Review / Article / Reddit), the outlet name, the named campus location, and a "View source ↗" link opening the original URL in a new tab.

**Sample interaction transcript**

```
User:    Where can UF students find food after midnight?

System:  UF students have a few options for late-night food. Checkers on University
         Avenue is open until 5am, but be prepared for long lines around 3-4am.
         McDonald's, located on Archer Road, is open 24/7 and starts serving
         breakfast at 4am. Taco Bell on Archer Road typically closes at 3am,
         although hours may vary. Domino's on 13th Street is another option,
         but it closes at 2am.

         (7_alligator_mealplans_atlernative.txt, 12_reddit_late_night.txt,
          5_alligator_broward_old.txt, 2_restarauntji_gator_corner.txt,
          1_yelp_broward_dining.txt)

Sources: [Article]  The Alligator    UF Dining / Bite Club             View source ↗
         [Reddit]   Reddit r/ufl     Gainesville Late-Night Dining     View source ↗
         [Article]  The Alligator    Norman Tent Dining (Broward)      View source ↗
         [Review]   Restaurantji     Gator Corner Dining Center        View source ↗
         [Review]   Yelp             Broward Dining Hall               View source ↗
```

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

The system prompt given to `llama-3.3-70b-versatile` contains five explicit rules, enforced as non-negotiable constraints rather than suggestions:

```
1. Answer ONLY using the numbered context passages provided by the user.
2. Do NOT draw on your training knowledge about UF dining, Gainesville
   restaurants, or meal plan pricing. Treat everything you know from training
   as if it does not exist.
3. If the context passages do not contain enough information to answer the
   question, respond with this exact sentence and nothing else:
   "I don't have enough information in my sources to answer that."
4. Do NOT guess, estimate, or fill in details absent from the context.
5. Do NOT reference passage numbers, passage positions, or source names.
   When opinions differ, use natural phrases like "opinions are mixed" or
   "some prefer X while others prefer Y" - never point back to the structure
   of the context you were given.
```

In addition to the prompt, grounding is enforced structurally before the LLM is called: any retrieved chunk with a cosine distance above 0.70 is dropped. If no chunks pass that threshold, the "not enough information" reply is returned directly without an API call at all. This means the LLM never sees noise chunks and cannot be led off-topic by loosely related text.

**How source attribution is surfaced in the response:**

Source attribution is entirely programmatic - it is never generated by the LLM. After the model returns its answer, `generate.py` iterates over the filtered chunk metadata and builds a deduplicated list of source dicts (`source`, `location`, `url`, `doc_type`, `filename`). `app.py` then renders this list in two places: a source filename line appended inside the answer card in parentheses (e.g. `4_alligator_broward_renovated.txt, 2_restarauntji_gator_corner.txt`), and a formatted sources table below the answer showing the outlet name, location badge, and a "View source ↗" link. Because these are built from chunk metadata rather than parsed from the LLM response, they cannot hallucinate or mis-cite a source.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about food quality at Gator Corner compared to Broward? | Gator Corner rated higher overall; one student now prefers The Eatery @ Broward post-renovation | Noted Gator Corner has abundant, fresh food; Broward described as "hit-or-miss"; mentioned one student now prefers The Eatery @ Broward over Gator Corner | Relevant | Partially accurate |
| 2 | Are there vegan options at UF dining halls, and how do students rate them? | Options exist but are limited; chef is adding more entrees; Gator Corner has dedicated vegan section | Confirmed vegan bar exists with high-quality ingredients; students find entrees lacking; chef is working to expand options | Relevant | Accurate |
| 3 | How much does a UF meal plan cost and is it worth buying? | Plans range $1,120–$3,150/semester; Reddit strongly advises against buying one | Returned "I don't have enough information in my sources to answer that" - retrieved chunks discussed sentiment but contained no dollar amounts | Partially relevant | Inaccurate (declined) |
| 4 | What food options are available at the Reitz Union? | Panda Express, Starbucks, Halal Shack, Baba's Pizza, Subway, Mi Apa | Listed Mi Apa, Panda Express, Starbucks, Halal Shack, Baba's Pizza, Subway, and a market; also mentioned meat carving stations and a Fresh Mex Burrito Bar | Relevant | Accurate |
| 5 | Where can UF students find food after midnight? | Taco Bell (~3 am), Checkers (until 5 am), McDonald's (24/7), Gumby's (~3 am), Wawa, Flaco's Tacos | Listed Checkers (until 5 am), McDonald's (24/7, breakfast at 4 am), Taco Bell (~3 am), Domino's (until 2 am); missed Gumby's, Wawa, and Flaco's | Relevant | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

"How much does a UF meal plan cost and is it worth buying?"

**What the system returned:**

"I don't have enough information in my sources to answer that." - despite retrieving four chunks from sources that explicitly discuss meal plans, including a Reddit thread titled "New UF Meal Plans Breakdown" and an Alligator article on meal plan alternatives.

**Root cause (tied to a specific pipeline stage):**

The failure is in chunking, not retrieval. The Reddit meal plan thread (`10_reddit_campus_dining.txt`) contains pricing information, but that information is spread across multiple comment chunks. The specific dollar amounts ($1,120–$3,150) landed in a chunk that ranked outside the top-5 retrieved - it was outcompeted by chunks about meal plan sentiment ("I highly recommend no one ever get a meal plan") which are semantically closer to the query. The LLM correctly refused to answer because none of the five chunks it received contained actual prices, even though that data exists in the corpus. This is a retrieval coverage failure caused by k=5 being too small for a multi-faceted question (cost AND worth) where the two sub-answers live in separate chunks.

**What you would change to fix it:**

Increase k to 8–10 for this query type, or implement query decomposition - split "how much does it cost" and "is it worth it" into two separate retrievals and merge the results before passing to the LLM. A metadata filter on `doc_type="reddit"` and `filename="10_reddit_campus_dining.txt"` could also be used to guarantee the pricing chunk is always included for cost-related queries.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

Defining the chunking strategy in planning.md before writing any code forced me to think through the unit of meaning for this corpus: a single person's opinion about a single location, before I had to implement it. When I was building `chunk.py`, I already knew the split priority (review boundaries first, then paragraph breaks, then character limit) because I had worked it out in the spec. Without that, I likely would have defaulted to a naive fixed-character split and only discovered the location+opinion pairing problem after running retrieval tests.

**One way your implementation diverged from the spec, and why:**

The spec planned for the context passed to the LLM to use numbered passage labels (`[1]`, `[2]`, `[3]`) to distinguish chunks. During testing I found that the model used those numbers to reference passages directly in its answers ("according to passage [1]…"), which surfaced internal pipeline structure to the user. I removed the numbering entirely and replaced it with plain paragraph breaks, then updated the system prompt to ban all passage-position references. The divergence was driven by observed output quality, not a flaw in the original plan. The spec assumed the model would treat the numbers as internal scaffolding, but in practice it treated them as citable identifiers.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* The Retrieval Approach section from planning.md, the architecture diagram, and the chunk dict schema (`text`, `source`, `location`, `url`, `doc_type`, `filename`). I asked Claude to implement `embed.py` with `build_index()` and `retrieve(query, k=5)`, using `all-MiniLM-L6-v2` and a persistent ChromaDB collection with cosine similarity.
- *What it produced:* A complete `embed.py` with batched inserts, a skip-rebuild guard, and a `__main__` smoke test covering all 5 evaluation queries.
- *What I changed or overrode:* I directed Claude to add two metadata fields not in the original spec - `chunk_index` and `chunk_total`, after reading the milestone requirement that each chunk must record its position within its source document. Claude's initial output did not include these.

**Instance 2**

- *What I gave the AI:* The Milestone 5 requirements, the constraint that grounding must be structurally enforced rather than just prompted, and the retrieve() function signature.I asked Claude to implement `generate.py` and `app.py` wired together end-to-end.
- *What it produced:* `generate.py` with a distance-threshold pre-filter and a strict system prompt, and `app.py` as a Gradio Blocks interface with an answer card, sources table, and example questions.
- *What I changed or overrode:* While testing I noticed the answers felt unnatural - retrieved document numbers were being cited inline, which didn't make sense in the output. The project requirements also specifically said cited sources should appear in the answer. I directed Claude to remove the passage numbering from the context format and update the system prompt to ban position-based references, then to append source filenames to the answer card programmatically from chunk metadata.