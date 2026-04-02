# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The UML started with seven classes where each one had a clear task: enums contained valid values, `Task` held the care work, `Pet` and `Owner` to create instances of both objects, and `Scheduler` was the only thing allowed to produce a plan.

**b. Design changes**

The biggest fix was adding a back reference from `Task` to `Pet` and swapping the string timestamps for actual `datetime.time` objects so the scheduler could do real math instead of parsing strings.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler weighs three things: how many minutes the owner has, how urgent each task is (priority 1 to 5), and what time of day each task prefers.

**b. Tradeoffs**

The greedy knapsack picks tasks in priority order and stops the moment one task would go over the budget, which means a single long high priority task can crowd out several shorter ones that would have fit in the leftover time, but for a pet care app that tradeoff is fine because meds and vet visits should always win.

---

## 3. AI Collaboration

**a. How you used AI**

AI helped at every stage from sketching the UML to writing tests, and the prompts that worked best were concrete and outcome focused rather than vague and open ended.

**b. Judgment and verification**

When AI wanted to store the time budget directly on `Scheduler` I rejected it because that value would silently drift away from `Owner.time_available_minutes`, so I traced every call site to make sure the budget always comes straight from the owner.

---

## 4. Testing and Verification

**a. What you tested**

The 32 tests hit the parts most likely to contain errors, such as recurrence date math (especially the Friday to Monday skip), budget boundary conditions, sort order, and both flavors of conflict detection.

**b. Confidence**

Sitting at 4 out of 5 because the core pipeline is solid and all tests pass, though the UI layer, the midnight overflow edge case, and a full end to end integration test are still untouched.

---

## 5. Reflection

**a. What went well**

Giving each scheduler method exactly one job made the whole thing surprisingly easy to test and debug in isolation.

**b. What you would improve**

The greedy selector can sacrifice several short useful tasks just to fit one long one, so the next version would try a smarter combination strategy instead.

**c. Key takeaway**

Drafting a UML before writing any code was genuinely worth it because AI becomes way more useful when it is filling in a structure you already understand rather than inventing one from scratch.
