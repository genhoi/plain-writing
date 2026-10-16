# Text for people

Translation of [skill/SKILL.md](../../skill/SKILL.md). The Russian file is the one agents load; this
copy is for reading. The examples of jargon and the section names are Russian by design: the rules
are written for Russian texts.

## Who reads it

The reader opens the text without our chat: a developer from another team, a tester, a lead a month
later, me in a new session. They do not know which branches we compared, what we decided on a call,
what `NP-35` is, or why we took this on at all. The text has to work on its own.

Before the first line, decide who reads it and what they will do with it. A developer needs a
technical description: what changes in behaviour, in data and in API contracts. A tester will walk
through a scenario on the staging server and needs steps and the expected result; class names get in
their way. A lead or the business needs a decision: why do this and what it gives. A colleague in a
messenger needs the question itself. If there are several readers, each gets their own section.

The main thing before publishing: read it as a stranger and ask of every sentence "will a person
who never saw the chat understand this?". If not, rewrite it or throw it out. How to do that for an
important text is in the section "Proofreading".

When handing a task to a tester, read its description by the same rules: a colleague or another
model may have written it. If it does not tell what to check, add a "How to verify" comment.

## What to throw out

- History: "cut out of branch X", "after the review of architecture Y", "earlier we wanted Z". The
  reader needs the result, not the path to it. The same in a document: no log of checks, no run
  dates, no numbers of test orders. A document says how things work, not how we got there.
- Internal identifiers without explanation: registry decision numbers, codes of agreements, names of
  experimental branches. Either explain in the same sentence or remove. A task or MR number as a
  link, or in brackets after a statement, may stay: it is a pointer for those who want details.
- Sections "Не входит" (out of scope), "Что осталось за бортом" (left out), "Что не сделано" (not
  done). The reader did not ask. If a limitation is real, it goes in one paragraph with the reason.
- Self-assessment: "minimal", "very useful", "carefully", "honestly". Let the reader judge.
- Lists of alternatives we rejected, and promises for the future.
- Risks and remarks "just in case". Keep what is confirmed by code or a measurement and changes the
  reader's decision. Drop trifles, procedure steps with no purpose and guesses like "what if the
  other team does not do it".
- Template headings for the sake of headings. A heading is needed when a different question sits
  under it.

## Words

- Do not invent terms. If a new word is needed ("operation key"), say in the same sentence what it
  is. Better to call the thing what the code or the product calls it: `gateway_transaction_id`, the
  "Pay on delivery" tab.
- Words that appeared during our work are new to the reader: names of steps, nicknames of options,
  names from other agents' reports ("reconciliation", "historical run", "cabinet"). We are used to
  them, so we do not notice them. Replace them with the name from the code or the product, or
  explain them.
- One word, one meaning across the whole text. If "layout" already means a group of payment methods,
  another concept gets another name.
- No jargon and no calques from English: not "fail-closed" but "refuses when in doubt"; not "spike"
  but "a one-day trial"; not "backoff" but "a pause between retries"; not "idempotent" but "a repeat
  changes nothing". If you would have to explain the word to a new colleague, replace the word with
  the explanation.

## Facts

- Every statement about how the system works now is verified against the code before publishing. A
  miss, as an example: I wrote "the gateway callback", but we poll the gateway ourselves; the reader
  stopped trusting the text at once.
- Statements about staging and production are verified on staging and production: a different
  service from the one whose code we read may be running there. Facts from old notes and memory are
  re-checked or left out.
- Give a consequence its condition. Not "every order will fail" but "with prepayment switched off,
  every order with paid packaging will fail".
- Give a conclusion its reason. The reader did not see what we read, and "you push because of
  composer.lock" is a cipher to them. Say what exactly is in the way and why only they can do it.
- One concrete example with numbers beats a paragraph of generalities: "a delivery prepayment will be
  recorded as payment for the whole order, the order becomes `paid` for 600 ₽ and leaves for the
  accounting system". Show a problem on an order from production rather than with a measurement on
  your own machine: it shows whether we are fixing the right thing. Leave out the customer's personal
  data.
- Links are full addresses one can follow. A link to a line of code points to a commit, not a
  branch: after the merge the lines move.

## Shape

The first line is the conclusion or the goal: what happened, what is needed from the reader, why the
task exists. Details come after.

- Task: **Problem** (what breaks and why it is so now, with an example) → **What to do** (numbered
  items for the developer: what has to change in behaviour, data or an API contract; class and method
  names only where the place cannot be found without them, the code structure changes fast) → **How to verify** (for the
  tester: what to set up, for example which flag to switch on and where; steps on the staging
  server in the product's words; what should happen; no class names and no unit tests, the tests are
  described in the MR; if the change is not visible from outside, which part of the product to run to
  check that nothing broke) → **Limitation** (only if real, with the reason).
- A task the business reads: first, in plain words, why do it and what it gives.
- MR or PR description: why, what changed in behaviour for all users, not only for those it was made
  for, how it was verified: tests and a check on staging. No retelling of the diff file by file. If the project has
  an MR template, fill it in; these rules apply inside it.
- A change to an API response: an example of the response "now" and "after", and where to take what.
- Review comment: the answer to the question in the first sentence, then why. No preamble.
- Your own change request in a review: one thread per change, attached to a line. The first phrase is
  what to change, then why and whether it blocks the merge.
- A reply to a tester's question ("is the task still needed", "what to test"): the answer first, then
  the steps to reproduce, what happens now and what happens after the fix.
- A messenger message, including one to forward: separate from the explanations for the user, one
  block that is copied whole; in a chat that is a code block. Inside, no markup and no quotes: the
  messenger will not show them. Address the recipient: "Is that size fine for you?", not "Is that size
  fine for them".
- A document, a README, a page for another team: who is who, if the text involves more than two
  systems or teams.
- Report to the user: after the first line, only what changes their next action.
- Short sentences, verbs. No asides in the middle of a thought, in brackets or after a dash: move
  them into a separate sentence. Code names only where the reader will go. Numbers: those that change
  a decision or are needed to check the result.
- A task is short. If it has two independent things in it, it is two tasks.
- If it is agreed to mark texts as prepared by AI, one line at the end, no more.

## Proofreading

A task, an MR description, a document and anything that goes to another team is read through the
reader's eyes before publishing. An author with our context does not see their own gaps, so it is
better when someone without it reads.

If you can start a separate agent without our conversation, give it only the text and the reader's
role: "you are a tester and will check by this text on staging". There can be two or three readers.
Ask it to list what is unclear without the chat; where parts of the text contradict each other;
which word has two meanings; which names are not explained; without which step the reader cannot act.

Do not hand it your conclusions: it will take them as facts. Check its findings against the code: it
can be wrong too, or invent a number. If you cannot start an agent, reread the text yourself by the
same list, for each reader in turn.

## Example

`skill/reference/task-before-after.md` is a breakdown of a task description before and after the
rules, with links to both texts; `skill/reference/mr-before-after.md` is the same for an MR
description. Open one before writing a task or an MR.
