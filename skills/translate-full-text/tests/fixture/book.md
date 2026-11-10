---
title: "The Quiet Workshop: Notes on Making Things"
author: Mara Ellison
lang: en
identifier: "ISBN 9780000000000"
date: 2026
publisher: Sample Press
---

# Copyright

Copyright © 2026 by Mara Ellison. All rights reserved. No part of this sample book may be reproduced without permission. Published by Sample Press. Printed nowhere, because it only exists as a test fixture.

# Preface

This little book collects notes I wrote in the margins of my own workshop over many winters. None of the ideas are new, but writing them down made me notice how often I forget them when a project gets difficult.

# Chapter 1: Starting Small

Every project begins with a bench that is too crowded. Before you cut anything, clear the surface and lay out only the tools you will need for the first hour of work.

![The workbench after it has been cleared for the first hour of work.](bench.png)

I keep a simple table of the habits that matter most at the start of a project:

| Habit | Why it matters | Time it takes |
|-------|----------------|---------------|
| Clear the bench | You can see what you are doing | Five minutes |
| Sharpen one tool | A dull edge hides your mistakes | Ten minutes |
| Write the goal down | The goal will drift if you do not | One minute |

> Make the first cut small enough that you would not mind making it again.

The quote above came from my teacher, who never once let me start with the hardest joint.[^teacher] She believed that confidence is a material, like wood or glue, and that you have to collect enough of it before the real work begins.

[^teacher]: She ran a furniture workshop for thirty years and refused to own a single power tool.

# Chapter 2: Measuring Progress

Progress in a workshop is hard to see from one day to the next. I measure it with a rough score that rewards finished steps more than hours spent:

$$
S = \frac{\text{finished steps}}{\text{planned steps}} \times 100
$$

When the score stops rising for three days in a row, I stop and ask what is blocking me. Usually the answer is one of these:

- a tool that needs repair
- a decision I have been avoiding
- a step I planned badly in the first place

I also keep a tiny script that adds up the score for each week:

```python
def weekly_score(finished, planned):
    return round(finished / planned * 100)  # rough, but honest
```

![A chart of weekly scores across one long winter.](chart.png)

The chart shows the same pattern every year: a slow start, a long middle where nothing seems to move, and a sudden finish when all the small steps come together at once.

# Bibliography

- Ellison, M. (2019). *Bench Notes*. Sample Press.
- Okafor, T. (2021). *The Patient Joint: Essays on Furniture Making*. Fieldstone Books.

# Index

bench, 3, 7; confidence, 9; progress, 11–14; score, 12; teacher, 9
