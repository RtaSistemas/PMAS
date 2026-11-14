# PMAS Writing Guide (ASD-STE100, 80% profile)

This guide tells you how to write English text for PMAS.
It applies to the user interface (`frontend/lang/en.js`), the documentation, and API error messages.
The Portuguese text (`frontend/lang/pt.js`) is a faithful translation of the English text.

PMAS follows ASD-STE100 Simplified Technical English with a practical profile.
The target is 80% of the sentences that pass the automatic check.
The profile has no dictionary check, because PMAS needs its own technical terms.

## Rules that PMAS checks

| # | Rule | Limit |
|---|------|-------|
| 1 | Write short sentences. | 20 words for an instruction, 25 words for a description |
| 2 | Use the active voice. | Do not write "is saved" - write "the system saves" |
| 3 | Do not use contractions. | Write "do not", not "don't" |
| 4 | Do not use filler or Latin words. | Do not use "please", "simply", "just", "etc.", "e.g.", "i.e." |
| 5 | Do not use vague verbs. | Do not use "should", "might", "may" - use "must" or "can" |

## Rules that you check by hand

1. Write one instruction in each sentence. Start the sentence with a verb ("Click Save.").
2. Use the same word for the same thing. Do not use two names for one object (see the terms below).
3. Keep the articles ("the", "a"). Do not remove them.
4. Do not use more than 3 nouns in a row. Write "the budget alert threshold", not "the project budget alert threshold value".
5. Do not use phrasal verbs ("set up", "carry out"). Use a simple verb ("install", "do").
6. Write a paragraph of 6 sentences or fewer.
7. Use numerals for numbers ("3 cycles").
8. State the result after each step ("The system shows the list.").
9. Use "must" for a required action. Use "can" for a possible action.
10. Write an error message in two parts: what is wrong, then what the user must do.

## Approved terms

| Use | Do not use |
|-----|------------|
| cycle | period, billing period |
| PEP | WBS code, project code |
| timesheet | hour sheet, time sheet |
| quarantine | hold, review queue |
| baseline | locked budget, snapshot |
| collaborator | resource, employee |
| import | upload (in a button), ingest (in the interface) |
| administrator | admin (in sentences) |

## Examples

| Before | After |
|--------|-------|
| `Please note that no PEPs with budget could be found.` | `The system found no PEP with a budget.` |
| `Select a cycle or PEP in the filters and then simply click Load.` | `Select a cycle or a PEP. Click Load.` |
| `The file couldn't be imported because it is too large.` | `The file is too large. Use a file of 20 MB or less.` |

## How to check

```bash
python scripts/ste_check.py docs/STE-GUIDE.md frontend/lang/en.js
```

The script prints the percentage of sentences that pass rules 1 to 5.
Keep each new or changed file at 80% or more.
