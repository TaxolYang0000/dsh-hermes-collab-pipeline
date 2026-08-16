# Where Should Coding Agent Go Next?

## — Why We Need a Multi-Agent Discussion Architecture

> **Original language: Chinese（原始版本为中文）**
> 中文版：[coding-agent-下一步要怎么走.md](coding-agent-下一步要怎么走.md)

---

## 1. The Starting Point: Human Energy Is the Bottleneck

The speed at which AI produces output has already outpaced the speed at which humans can review it. In one hour, a single Agent can write a complete technical proposal, generate thousands of lines of code, and produce a dozen documents — how long does a human need to read through all of it? Far more than an hour. In the single-Agent model, you are both the user and the reviewer; every piece of output has to pass through your eyes. The faster the Agent works, the heavier your review burden becomes.

This is the most basic contradiction: AI has automated "doing the work," but it has not automated "reviewing." Review is still a labor-intensive activity, and the volume of review grows linearly with AI's speed. The slowest, most expensive, and most easily exhausted link in the entire pipeline is still a human.

So the first reason we need a multi-Agent discussion architecture is not cognitive — it is about energy. One person watching a single Agent is already tiring; watching several is impossible. To free people from process supervision and further improve work efficiency, review must be automated — Agents reviewing Agents.

## 2. Review Is a Single Point of Failure: Bad Output Flows All the Way Through

In the single-Agent model, output quality depends entirely on the Agent itself. If it thinks it wrote it correctly, it ships it — no one has ever looked at it from a second perspective. A model's self-evaluation is unreliable: it has a systematic optimism about its own output and cannot see the false premises it buried.

Manual review can partially solve this problem, but two issues remain:

First, not enough energy. The volume of AI output is what it is; a human cannot review line by line, word by word.

Second, not enough context. The toolchains, codebases, and contexts AI works with are enormous — almost impossible to be fully familiar with. Many subtle errors are nearly impossible for a human to spot.

So the reality is: a large amount of AI output gets used in a state where "no one has reviewed it." A wrong assumption moves into the next step, bad code ships, a wrong direction wastes an entire iteration. Review is not a luxury — it is the lifeline of quality, and right now that lifeline rests on a human.

This is the second reason we need a multi-Agent discussion architecture: review must move from "a human's obligation" to "a system's mechanism." Let another Agent do the reviewing — it has the full toolchain, it can read the codebase, it can run tests. It reviews faster, deeper, and more completely than a human. The human only needs to review the conclusion it produces.

## 3. Agent-to-Agent Review Must Be Reliable: The False Consensus of Two-Plate Grinding

So having Agents review Agents is right and necessary — but is two Agents reviewing each other enough? No. The machining industry answered this question long ago.

In precision machining, standard flat surfaces are made by scraping. Two plates ground against each other can never yield a high-precision plane: if one is convex and the other concave, they will mate perfectly — yet neither is flat; the error is not removed, it is mutually adapted. Three plates ground in a closed loop (A against B, B against C, C against A) are required: any convexity on one plate is exposed by the other two, and after cycles all three may converge toward a true plane.

Two-Agent cross-review is two-plate grinding. A reviews B, B reviews A — two Agents can validate each other's blind spots and reach a conclusion that is "consistent yet wrong": they did not find the correct answer, they adapted to each other's errors. This is especially true for same-family models: models from the same vendor share the same training data and the same kind of reasoning bias. What A cannot see, B cannot see either. A reviewing B and B reviewing A is no review at all.

To break false consensus, a closed loop is needed: at least three parties reviewing in a cycle (A reviews B, B reviews C, C reviews A), so any single point of error is caught by a third party that does not share its bias. Heterogeneity — not just different harness architectures, but different models — further lowers the probability of shared blind spots. This is why "automated review" is not simply "two Agents looking at each other" — it must be a structure, a closed-loop structure.

## 4. The Multi-Agent Discussion Architecture: Review Should Have a Fixed Mechanism

Turning review into a mechanism requires, in my current view, four elements — all four are indispensable:

First, independent generation (round start). The question is dispatched to all parties, each produces a proposal first, and they cannot see each other's. Seeing another's proposal first anchors you — the first proposal becomes everyone's frame of reference. Independent generation ensures each party enters the discussion with a genuinely independent position, not with an echo of the first proposal.

Second, closed-loop cross-review. All proposals are distributed in full; each party must state, for every other proposal, what it supports, what specific problems it sees, and what improvements it suggests. Writing only "I agree" does not count. This is the three-plate closed loop turned into a protocol: A reviews B, B reviews C, C reviews A. Forcing "Pros and Cons" turns formal agreement into genuine comparison.

Third, bounded convergence (synthesize). Take new opinions into the next round until convergence. Convergence must be explicitly defined — in my current view, any one of three conditions stops the loop: consensus reached, a fixed number of rounds completed, or three consecutive rounds with no change. An unbounded discussion becomes an infinite money sink; without a drift-detection mechanism, the discussion becomes a loop of people talking past each other.

Fourth, human final judgement. The output of the discussion is a "unified recommendation plus a list of residual disagreements," and a human makes the final decision.

Compared with today's prevailing single-Agent form, the human's role changes under this architecture: from "reviewing every piece of output" to "reviewing only the final conclusion."

## 5. What This Architecture Means: Human Energy Should Be Spent on Final Judgement

What humans value most is judgement. Final judgement and process review consume judgement in completely different ways:

Process review faces a flood of details — is the code right, is the documentation complete, is anything missing. It is manual labor that consumes attention, and AI is faster than humans, so humans are forever chasing.

Final judgement faces a small amount of critical information — the three proposals, the records of exchange, the points of disagreement. This is judgement work that consumes insight; AI has already done the complete work, and the human only needs to decide.

The value of the multi-Agent discussion structure is moving human energy from "reviewing details" to "making decisions." Details are cross-reviewed by Agents; the human only looks at: where proposals conflict, why a disagreement was not resolved, which proposal best matches the goal. Humans review less, but each item is more valuable and more directly to the core.

This is not taking decision authority away from humans — it is organizing the information needed for a decision completely, and putting it in front of them.

## 6. Discussion Must Be Tiered: The AI Budget Problem

Discussion is not cheap. Every round is multiple model calls, and cost scales with the number of rounds. So discussion must be tiered, enabled according to task value:

Low-risk, clearly-defined tasks: execute directly. One Agent finishes, and another either skips review or does a light review.

Medium-risk tasks: dual-model cross-review. One implements, one reviews, with forced heterogeneous pairing.

High-risk, ambiguous, strategic questions: full discussion. Three parties independently generate, closed-loop cross-review, bounded convergence, human final judgement.

The point of tiering: spend the budget where it truly matters. Opening a three-party discussion for "write a README" is waste; opening one for "architecture selection" is right. There is only one criterion — how costly is it if this decision is wrong. If the cost is high, discuss; if it is low, execute directly.

Tiering is also part of the energy budget: human energy is finite, and the discussion structure must ensure that every instance of deep human review and discussion is spent on a decision worth it.

## 7. Implementation Form

In my testing so far, the discussion structure ultimately lands on kanban, because kanban is already a proven hard record surface:

Each round equals a group of kanban tasks (round start creates tasks, each party claims and produces, writes back its position).

Cross-review equals dependency relationships (task_links natively expresses "review task depends on implementation task").

Convergence judgement equals a watcher-side state machine (any of the three conditions triggers automatic synthesize).

Output archiving equals the unified recommendation plus the residual-disagreement list, stored as a pre-decision for the task — reusable and auditable.

Every step is recorded, every exchange leaves a trace. Discussion is not a chat room; it is an engineering structure with state machines, audit trails, and budgets — you can go back at any time to see how any decision was discussed.

## Conclusion

Back to the starting point: human energy is the bottleneck, review is the single point of failure. What the multi-Agent discussion architecture does is take review off the human's shoulders and turn it into a system mechanism; free human energy from process supervision and keep it only for final judgement. The three-plate grinding of Agents is not a ritual — it is mathematics: two plates can adapt to each other into perfectly matching curved surfaces, and only a third plate can expose the illusion. Independent generation ensures positions are genuine, closed-loop cross-review ensures errors have nowhere to hide, bounded convergence ensures the discussion ends, and human final judgement ensures decision authority stays with humans. The multi-Agent discussion architecture is not making simple things complicated — it is a possible solution to the problem that "human energy is finite" may eventually limit the use of Coding Agents.

## Appendix: Critique of This Article, and the Conditions Under Which It Holds

Think it's perfect? Time to pour some cold water.

This article's argument is not without premises. We assumed the review workload is exogenous and unremovable — but it is actually a function of workflow quality: with clear prompts, well-decomposed tasks, and sufficient SOP injection, output quality is controlled at the source, and end-of-line review can degrade into sampling verification (for linear work, checking 5% validates 95%; for nonlinear work, 20% validates 80% — the Pareto principle). We assumed review must be done by another Agent and that AI review is comprehensively superior to human review — but the cost structure of human sampling review and human-machine division of labor is completely different. We borrowed the scraping analogy, but scraping has an objective ground truth (flatness); AI cross-review does not — what it converges to may be merely majority consensus, not truth. We assumed that forcing "Pros and Cons" distinguishes formal agreement from genuine comparison, but who judges whether a challenge is real? AI does not possess truth, and the authority is not present. We assumed human final judgement is reliable, but human decision-making is equally limited — judging a black-box conclusion is not much different from trusting a black box. We assumed the benefits of discussion exceed the token cost, yet we never established a measurable ROI — converting token consumption into the human brain-hours needed to perform equivalent verification, then into market labor value; this ledger was never calculated. And the root of all this is a deeper assumption: the user cannot control AI's output process, so the only option is to catch problems at the end.

So when is this article actually true? The assumptions it critiques form a tree branching from a single root: the user cannot control AI's output process. "Cannot control" has four meanings; if any one is true, the article's premise holds: physically cannot (AI output complexity exceeds the human brain's comprehension ceiling), capability-wise cannot (the user is not an expert in this domain, or cannot surpass AI in it), scale-wise cannot (the task volume exceeds what one person can maintain), information-wise cannot (the process is unobservable — black-box models, distributed execution). Conversely, a person who can decompose tasks, inject SOPs, and do sampling verification is outside this premise's coverage. So the article's true readers are not "people who use AI" — they are "people who are used by AI."

Going further, once review is handed to AI, the technical linchpin of the whole architecture appears: does AI cross-review have ground truth? The scraping analogy exposes its boundary here for the first time. Scraping has objective truth — flatness is a physical quantity, and three plates converge toward reality. AI cross-review has no such anchor: A says B's proposal has a flaw, B rebuts — who is right? Without an external standard, what it converges to may be only majority consensus, not truth. Only when verification can be automated — code has tests, mathematics has proof checkers, physics has simulators — does cross-review shift from spinning wheels to having a basis: A challenges B, B can rebut by running tests, challenges are checked against facts, and forcing "Pros and Cons" truly triggers comparison. This is the most fragile and most promising link in the whole article: it does not depend on argumentation — it depends on the maturity of the toolchain.

Above that is the human's position. When the process is handed to AI and verification to tools, the human retreats to final judgement. Is final judgement reliable? It depends on what is being judged. If what is judged is a black-box of technical details, the human lacks judgement; if what is judged is values, goals, preferences — which goals are worth pursuing, which trade-offs are ethical — that is the human's home turf, where AI has no training set. So the human's right of final judgement is not natural; it has a hidden condition: final judgement must fall in a domain where the human is genuinely strong. Otherwise, judging a black-box conclusion is no different from trusting a black box.

Finally, the economic ledger — the one that changes fastest over time. For the whole system to be worth it, token cost must be lower than human review cost, and the cost of error must be higher than the cost of discussion. This condition does not hold today — pure language cross-review burns tokens with no anchor. It may hold in the distant future — models get stronger, tasks get more complex, humans get relatively weaker, and tokens get cheaper. On the day the three lines converge, this article turns from vision into reality: the root condition holds (there are indeed many people who cannot control the process), the technical line opens (verification can be automated), and the economic line flips (AI cross-review is cheaper than human review).

Human society's peer review has run for centuries. It works because reproducible experiments act as an anchor outside the review system itself. What AI cross-review needs to do is move the same anchor into the machine world — when code has tests, proposals have simulations, and judgements have verification, multi-Agent discussion is no longer "covering garbage with bigger garbage" but genuine peer review.

---

Project repository: https://github.com/TaxolYang0000/agent-federation-platform

*I am not a student specializing in AI or CS. This article expresses some rough opinions; all discussion is welcome. This article is partially AI-generated, with wording reviewed and edited by a human.*

*This article is licensed under CC BY-NC-ND-SA 4.0.*
