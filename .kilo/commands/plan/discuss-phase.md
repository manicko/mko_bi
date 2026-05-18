---
name: discuss-phase
description: Gather context through adaptive questioning before planning
argument-hint: "<file_number>"
allowed-tools:
  - read_file
  - write_to_file
  - execute_command
  - list_files
  - search_files
  - ask_followup_question
---

<objective>
Extract implementation decisions that downstream agents need — researcher and planner will use DECISION_{file_number}.md to know what to investigate and what choices are locked.

**How it works:**

1. Analyze the problems in `C:\py_dev\mkobi\.ai\problems\CONTEXT_*.md` to identify gray areas (UI, UX, behavior, etc.)
2. Present gray areas — user selects which to discuss
3. Deep-dive each selected area until satisfied
4. Create DECISION_{file_number}.md with decisions that guide research and planning

**Output:** new file `.ai\problems\decisions\DECISION_{file_number}.md` — decisions clear enough that downstream agents can act without asking the user again
</objective>

<execution_context>
.kilo/skills/discuss-phase/SKILL.md
.ai/templates/decision.md
</execution_context>

<context>
**Study user problems in**:
`C:\py_dev\mkobi\.ai\problems\CONTEXT_*.md`


Study `C:\py_dev\mkobi\.ai\problems\decisions\DECISION_*md`
to define next free file number: {file_number} (required)


**Load project information:**
[AGENTS.md](C:\py_dev\mkobi\AGENTS.md)
[project rules](C:\py_dev\mkobi\.ai\context\**)
[specification](C:\py_dev\mkobi\docs\**)
[structure](C:\py_dev\mkobi\docs\STRUCT.md)
</context>

<process>
1. Keep {file_number} 
2. Check if DECISION_{file_number}.md exists (offer update/view/skip if yes)
3. **Analyze phase** — Identify domain and generate phase-specific gray areas
4. **Present gray areas** — Multi-select: which to discuss? (NO skip option)
5. **Deep-dive each area** — 4 questions per area, then offer more/next
6. **Write DECISION_{file_number}.md** — Sections match areas discussed
7. Offer next steps (research or plan)

**CRITICAL: Scope guardrail**

- Discussion clarifies HOW to implement, not WHETHER to add more
- If user suggests new capabilities: "That's its own phase. I'll note it for later."
- Capture deferred ideas — don't lose them, don't act on them

**Domain-aware gray areas:**
Gray areas depend on what's being built. Analyze the phase goal:

- Something users SEE → layout, density, interactions, states
- Something users CALL → responses, errors, auth, versioning
- Something users RUN → output format, flags, modes, error handling
- Something users READ → structure, tone, depth, flow
- Something being ORGANIZED → criteria, grouping, naming, exceptions

Generate 3-4 **phase-specific** gray areas, not generic categories.

**Probing depth:**

- Ask 4 questions per area before checking
- "More questions about [area], or move to next?"
- If more → ask 4 more, check again
- After all areas → "Ready to create context?"

**Do NOT ask about (KiloCode handles these):**

- Technical implementation
- Architecture choices
- Performance concerns
- Scope expansion
  </process>

<success_criteria>

- Gray areas identified through intelligent analysis
- User chose which areas to discuss
- Each selected area explored until satisfied
- Scope creep redirected to deferred ideas
- DECISION_{file_number}.md captures decisions, not vague vision
- User knows next steps
  </success_criteria>
