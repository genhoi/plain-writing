# Text for people

Translation of [skill/SKILL.md](../../skill/SKILL.md). The Russian file is the one agents load; this
copy is for reading. The examples of jargon and the section names are Russian by design: the rules
are written for Russian texts.

## Who reads it

The reader opens the text without our chat: a developer from another team, a tester, a lead a month
later, me in a new session. They do not know which branches we compared, what we decided on a call,
what `NP-35` is, or why we took this on at all. The text has to work on its own.

There is one check before publishing: read it as a stranger and ask of every sentence "will a person
who never saw the chat understand this?". If not, rewrite it or throw it out.

## What to throw out

- History: "cut out of branch X", "after the review of architecture Y", "earlier we wanted Z". The
  reader needs the result, not the path to it.
- Internal identifiers without explanation: registry decision numbers, codes of agreements, names of
  experimental branches. Either explain in the same sentence or remove.
- Sections "Не входит" (out of scope), "Что осталось за бортом" (left out), "Что не сделано" (not
  done). The reader did not ask. If a limitation is real, it goes in one paragraph with the reason.
- Self-assessment: "minimal", "very useful", "carefully", "honestly". Let the reader judge.
- Lists of alternatives we rejected, and promises for the future.
- Template headings for the sake of headings. A heading is needed when a different question sits
  under it.

## Terms and facts

- Do not invent terms. If a new word is needed ("operation key"), say in the same sentence what it
  is. Better to call the thing what the code calls it: `gateway_transaction_id`.
- No jargon and no calques from English: not "fail-closed" but "refuses when in doubt"; not "spike"
  but "a one-day trial"; not "backoff" but "a pause between retries"; not "idempotent" but "a repeat
  changes nothing". If you would have to explain the word to a new colleague, replace the word with
  the explanation.
- Every statement about the system's behaviour is verified against the code before publishing. A
  miss, as an example: I wrote "the gateway callback", but we poll the gateway ourselves; the reader
  stopped trusting the text at once.
- One concrete example with numbers beats a paragraph of generalities: "a delivery prepayment will be
  recorded as payment for the whole order, the order becomes `paid` for 600 ₽ and leaves for the
  accounting system".

## Shape

- Task: **Problem** (what breaks and why it is so now, with an example) → **What to do** (numbered
  items, each naming a class, table or method) → **How to verify** (tests and what to look at on the
  staging server) → **Limitation** (one, only if real, with the reason).
- MR description: why, what changed in behaviour for everyone (not only for the pilot), how it was
  verified. No retelling of the diff file by file.
- Review comment: the answer to the question in the first sentence, then why. No preamble.
- Report to the user: the result on the first line, then only what changes their next action.
- Short sentences, verbs, no thinking-aloud dashes and no parentheses. Code names only where the
  reader will go. Numbers only if they change a decision.
- A task fits on one screen. If it does not, there are two documents inside.
- If it is agreed to mark texts as prepared by AI, one line at the end, no more.

## Example

`skill/reference/task-before-after.md` is the same task description before and after the rules;
`skill/reference/mr-before-after.md` is the same for an MR description. Open one before writing a
task or an MR: the difference shows better than any rule.
