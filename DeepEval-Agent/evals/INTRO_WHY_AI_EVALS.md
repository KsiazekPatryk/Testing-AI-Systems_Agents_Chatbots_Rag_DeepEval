> 🇵🇱 **[Polska wersja tego dokumentu → poniżej](#wersja-polska)** · Powrót: [README projektu](../README.md)

# Introduction — Why AI Needs a Completely Different Kind of Testing

> **Read this before opening any test file.** This document sets the foundation for everything that follows. It answers four questions:
> 1. What exactly are we testing when we say "test an AI system"?
> 2. Why can't we test it the way we test traditional software?
> 3. What are Evals, and how does DeepEval implement them?
> 4. What is a Judge LLM and why do we need one?
>
> Once you're comfortable with these concepts, `test_agent.py` (the first test file) will make immediate sense.

---

## 1. What Exactly Is AI Testing?

When someone says "test a web application," you know exactly what that means — click a button, check the database, verify the response code. The system is well-defined: inputs go in, predictable outputs come out.

But AI systems are different. There is no single "AI application" shape. In this course, we deal with four distinct types of AI systems, each with its own testing challenges:

### 1.1 AI Agents

An AI Agent is an LLM that can **take actions** — it decides which tools to call, in what order, with what arguments, and then interprets the results to form a final answer.

**Example from our codebase:** `agent_plain.py` is a customer-support agent with two tools — `get_order_status()` and `get_refund_policy()`. When a user asks "Where is my order ORD-1042?", the agent must:
1. **Decide** that this is an order status question (not a refund question).
2. **Choose** the `get_order_status` tool.
3. **Extract** the order ID "ORD-1042" from the user's message and pass it as the argument.
4. **Interpret** the tool's response and formulate a helpful reply.

**What can go wrong:**
- The agent calls the wrong tool (asks for refund policy when the user wants order status).
- The agent calls the right tool with wrong arguments (passes "1042" instead of "ORD-1042").
- The agent calls the right tool, gets the right data, but misinterprets or garbles it in the final reply.
- The agent calls unnecessary extra tools, wasting time and money.
- The agent ignores its system prompt instructions (goes off-brand, gives long answers when told to be brief).

Every one of these failure modes needs a different evaluation strategy. That's why `test_agent.py` uses **TaskCompletionMetric** (did the whole job get done?) and **ToolCorrectnessMetric** (did it pick the right tool?).

### 1.2 MCP (Model Context Protocol) Tools

MCP is a protocol that lets AI agents connect to **external tool servers**. Instead of defining tools directly in code, the agent discovers tools dynamically from an MCP server at runtime.

**Example from our codebase:** `mcp_server.py` exposes a `get_shipping_options` tool via MCP. The instrumented agent in `agent_instrumented.py` connects to this MCP server at startup and adds the shipping tool to its toolkit alongside the regular Python tools.

**What's different about testing MCP:**
- The agent doesn't just call a local function — it calls a tool discovered at runtime from an external server.
- Tool names and descriptions come from the MCP server, not from the agent's own code.
- The agent must correctly identify that a user question about shipping should route to the MCP tool rather than the locally defined tools.

In `test_agent.py`, the fourth golden tests exactly this — it asks "What shipping options do you offer?" and expects the agent to call `get_shipping_options`, which is the MCP-served tool. The testing mechanics are the same (ToolCorrectnessMetric doesn't care whether a tool is local or MCP), but the *integration surface* is wider.

### 1.3 Chatbots (Multi-Turn Conversations)

A Chatbot maintains conversation history across multiple user messages. Unlike a single-turn agent that processes one question in isolation, a chatbot must remember what was said earlier and stay in character throughout.

**Example from our codebase:** `chatbot.py` is a multi-turn support bot. A user might say:
- Turn 1: "My order ID is ORD-1042."
- Turn 2: "Is it going to arrive on time?"
- Turn 3: "What was the ETA you just mentioned?"

The chatbot must carry context forward — it needs to remember the order ID from Turn 1 to answer Turn 2, and remember the ETA it provided in Turn 2 to answer Turn 3.

**What can go wrong:**
- The chatbot forgets information from earlier turns (memory failure).
- The chatbot breaks character — e.g., a customer support bot starts giving cooking advice.
- Individual turns are off-topic even if the conversation as a whole seems reasonable.
- The conversation technically progresses but never actually resolves the customer's issue.

These failures require **conversational metrics**: KnowledgeRetention, RoleAdherence, TurnRelevancy, and ConversationalGEval — all covered in `test_chatbot.py`.

### 1.4 RAG (Retrieval-Augmented Generation)

A RAG Agent doesn't rely on the LLM's training data to answer questions. Instead, it first **retrieves** relevant documents from a knowledge base, then uses those documents as context to generate an answer.

**Example from our codebase:** `rag_agent.py` has a vector store loaded with 9 policy documents (shipping, returns, cancellation, etc.). When a user asks "What is the return policy for electronics?", the agent:
1. **Retrieves** the top 3 most relevant policy documents from the vector store.
2. **Reads** those documents.
3. **Generates** an answer based on the retrieved content.

**What can go wrong — the RAG-specific failures:**
- **Hallucination:** The agent says something that isn't in the retrieved documents. The retrieval says "15 days" but the agent says "30 days."
- **Bad retrieval ranking:** The most relevant document is ranked 3rd while irrelevant ones are ranked 1st and 2nd. The LLM might miss the important one.
- **Incomplete retrieval:** The knowledge base has the answer, but the retriever failed to surface the right document.
- **Irrelevant answer:** The retrieved documents are fine but the agent goes off-topic in its response anyway.

RAG testing requires a specialized set of metrics (Faithfulness, ContextualPrecision, ContextualRecall, AnswerRelevancy) covered in `test_rag_agent.py`.

---

## 2. Why Traditional Testing Doesn't Work

### The Determinism Problem

Traditional software testing relies on one fundamental assumption: **the same input produces the same output every time.**

```
# Traditional test — this works because software is deterministic
assert add(2, 3) == 5          # Always true. Every time. Forever.
assert login("admin", "pass123") == "Welcome, admin!"  # Predictable.
```

You write an assertion. You run it 1000 times. It passes 1000 times. If it fails, something is broken.

Now try this with an AI agent:

```
# AI agent test — this DOES NOT work
response = support_agent("Where is my order ORD-1042?")
assert response == "Order ORD-1042 is Shipped. ETA: 2026-05-13."
```

**Why this fails:** Run this 10 times and you might get 10 slightly different responses:
- "Order ORD-1042 has been shipped and should arrive by May 13, 2026."
- "Your order ORD-1042 is currently shipped! Expected delivery: 2026-05-13."
- "I checked your order — ORD-1042 is on its way! It's expected to arrive by May 13th."
- "Great news! Order ORD-1042 has shipped. ETA is May 13, 2026."

All four responses are **correct**. All four convey the same information. But none of them match the exact string in the assertion. The test fails 100% of the time even though the agent works perfectly.

### Why AI Systems Are Non-Deterministic

LLMs generate text by **sampling from probability distributions**.

...It can produce different outputs for the same input. And with temperature > 0, the variation is intentional and by design.

### The String-Match Trap

The traditional testing instinct is to match strings:

```
# All of these are bad ideas for AI testing:
assert "shipped" in response.lower()        # What if it says "on its way"?
assert response.startswith("Order ORD")     # What if it says "Your order"?
assert len(response) < 100                  # Arbitrary, ignores content quality
```

You can play whack-a-mole with regex patterns and substring checks, but you'll never cover the full space of valid responses. And you'll spend more time maintaining your test assertions than actually testing the agent.

### What We Actually Want to Test

The question isn't "did the agent produce this exact string?" — it's:

- **Did the agent give the right information?** (semantic correctness, not string matching)
- **Did it use the right tool?** (behavioral, not output-based)
- **Was the response relevant to the question?** (semantic judgment)
- **Did it follow its instructions?** (compliance checking)
- **Was it efficient?** (step counting, not output checking)
- **Did it hallucinate?** (factual grounding against sources)
- **Was it safe, unbiased, and privacy-preserving?** (guardrails)

None of these can be answered with `assert response == expected`. Every one of them requires **judgment** — the ability to read the response, understand its meaning, and evaluate its quality.

This is where **Evals** come in.

---

## 3. What Are Evals? How Does DeepEval Work?

### Evals — The Concept

"Eval" is short for **evaluation**. In the AI world, an eval is a structured, repeatable process for measuring how well an AI system performs on a specific quality dimension.

Think of it this way:

| Traditional Testing | AI Evals |
|---|---|
| Binary: pass or fail | Scored: 0.0 to 1.0 |
| Exact match | Semantic judgment |
| Deterministic | Probabilistic |
| "Is the output correct?" | "How good is the output?" |
| Written by QA engineers | Judged by another LLM |

An eval doesn't ask "is this exactly right?" — it asks "how good is this, on a scale?" and then you set a **threshold** to decide what's good enough.

### DeepEval — The Framework

DeepEval is an open-source Python framework for evaluating LLM applications. It provides:

1. **Metrics** — Pre-built evaluation criteria (AnswerRelevancy, Faithfulness, ToolCorrectness, etc.) plus the ability to define custom criteria via GEval.
2. **Test cases** — Structured containers for inputs, outputs, and expected values (Goldens).
3. **A judge LLM** — An LLM that scores the outputs (explained in Section 4 below).
4. **Tracing/instrumentation** — Hooks into LangChain, OpenAI, etc. to automatically capture what the agent did (tool calls, intermediate steps, retrieved documents).
5. **A test runner** — Integration with pytest, or standalone `evaluate()` / `evals_iterator()` methods.

### How a DeepEval Evaluation Works — Step by Step

Here's what happens when you run a test file like `test_agent.py`:

```
Step 1: Define your test data
    ┌──────────────────────────────────────────────────────┐
    │  Golden(                                             │
    │      input="Where is my order ORD-1042?",            │
    │      expected_tools=[ToolCall(name="get_order_status")]│
    │  )                                                   │
    └──────────────────────────────────────────────────────┘
    A "Golden" is one test scenario — the input you'll send
    to the agent, plus any expected values to compare against.

Step 2: Choose your metrics
    ┌──────────────────────────────────────────────────────┐
    │  task_completion  = TaskCompletionMetric(threshold=0.7)│
    │  tool_correctness = ToolCorrectnessMetric()           │
    └──────────────────────────────────────────────────────┘
    Each metric knows how to evaluate one quality dimension.
    The threshold is YOUR definition of "good enough."

Step 3: Run the agent
    ┌──────────────────────────────────────────────────────┐
    │  support_agent("Where is my order ORD-1042?")        │
    └──────────────────────────────────────────────────────┘
    The agent runs for real — it calls tools, generates a
    response. DeepEval's instrumentation captures everything
    as a "trace" (the sequence of steps the agent took).

Step 4: The Judge LLM scores the trace
    ┌──────────────────────────────────────────────────────┐
    │  Judge (GPT-4o) examines:                            │
    │    - The user input                                  │
    │    - The agent's full execution trace                 │
    │    - The final response                              │
    │    - The expected values from the Golden              │
    │                                                      │
    │  It produces a score: 0.85                           │
    │  Threshold was 0.7 → PASS ✓                          │
    └──────────────────────────────────────────────────────┘
```

### How Scoring Works

Every DeepEval metric produces a score between **0.0 and 1.0**:

| Score | Meaning |
|-------|---------|
| 1.0 | Perfect — the output fully satisfies the metric |
| 0.7–0.9 | Good — minor issues but overall solid |
| 0.4–0.6 | Mediocre — significant room for improvement |
| 0.1–0.3 | Poor — major failures detected |
| 0.0 | Complete failure on this metric |

You set a **threshold** for each metric — this is your pass/fail line. If the score is at or above the threshold, the test passes. If it's below, the test fails.

**Threshold is a design decision, not a rule.** Different metrics and different use cases warrant different thresholds:

- **Quality metrics** (AnswerRelevancy, TaskCompletion, GEval): typically `0.7` — you want high quality but allow some flexibility.
- **Safety metrics** (Bias, Toxicity, PII): set at `0.5` in our files — these scores can be noisy, but any production system should push these higher.
- **Efficiency metrics** (StepEfficiency): typically `0.5` — agents rarely take the theoretically optimal path, so you allow more slack.

### Two Types of Metrics — Deterministic vs. LLM-Judged

Not all metrics use a judge LLM:

**Deterministic metrics** calculate the score using exact logic — no LLM involved:
- `ToolCorrectnessMetric` — compares actual tool calls against expected tool calls. It's a set comparison. Either the agent called `get_order_status` or it didn't. No interpretation needed.

**LLM-judged metrics** ask another LLM to evaluate the quality:
- `TaskCompletionMetric` — there's no formula for "did the agent complete the task." It requires understanding the user's intent, the agent's actions, and whether the outcome makes sense. Only an LLM can judge this.
- `AnswerRelevancyMetric`, `FaithfulnessMetric`, `GEval`, all safety metrics — all require semantic understanding that only an LLM can provide.

---

## 4. The Judge LLM — Why We Use a Second LLM to Grade the First

### The Core Idea

If we can't use string matching to evaluate AI outputs, and we need semantic understanding to judge quality, who does the judging? The answer: **another LLM**.

This is the **Judge LLM** (also called the "evaluator model"). It's a separate LLM whose job is to read the agent's work and score it.

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│   User       │       │   Agent LLM     │       │  Judge LLM  │
│   Question   │──────▶│   (under test)  │──────▶│  (scorer)   │
│              │       │                 │       │             │
│ "Where is my │       │  Calls tools,   │       │ Reviews the │
│  order?"     │       │  generates      │       │ trace and   │
│              │       │  response       │       │ output,     │
│              │       │                 │       │ gives score │
└─────────────┘       └─────────────────┘       └─────────────┘
                                                       │
                                                  Score: 0.85
                                                  PASS ✓
```

### Why Not Just Have the Agent Grade Itself?

Using the same LLM to both generate and evaluate creates a conflict of interest — like grading your own exam. Research has shown that LLMs tend to rate their own outputs more favorably than outputs from other models. This is called **self-evaluation bias**.

### Cross-Vendor Setup — Our Approach

In our test files, we intentionally use **different providers** for the agent and the judge:

| Role | Model | Provider | Purpose |
|------|-------|----------|---------|
| Agent LLM (system under test) | Claude / GPT-4o | Anthropic / OpenAI | Runs the agent, generates responses |
| Judge LLM (evaluator) | GPT-4o | OpenAI | Scores the agent's performance |

This cross-vendor setup means:
- The agent (the student) and the judge (the teacher) are from different "families."
- The judge has no bias toward the agent's outputs.
- The evaluation is more objective and trustworthy.

### What the Judge Actually Does

When a metric like `TaskCompletionMetric` runs, here's what happens internally:

1. DeepEval constructs an **evaluation prompt** — a carefully designed prompt that tells the judge LLM exactly what to evaluate and how.
2. The prompt includes the user's input, the agent's full trace (tool calls, intermediate steps, final response), and the evaluation criteria.
3. The judge LLM reads everything and produces:
   - A **score** (0.0 to 1.0)
   - A **reason** (textual explanation of why it gave that score)
4. DeepEval compares the score to the threshold and reports pass/fail.

The evaluation prompts are designed by DeepEval's authors using prompt engineering best practices — you don't write them yourself. Each metric has its own evaluation prompt template optimized for that specific quality dimension.

### The Judge Is Not Perfect — And That's OK

The judge LLM is itself an AI, so it's also non-deterministic. The same agent output might receive a 0.78 on one run and a 0.82 on the next. This is why:

- **Thresholds should have margin.** If your true minimum acceptable quality is 0.8, set the threshold to 0.7 to absorb scoring variance.
- **Run evals multiple times** when the results are borderline.
- **Look at the reasons**, not just the scores. DeepEval's metrics often provide a textual explanation of the score — this is more informative than the number alone.

---

## 5. Putting It All Together — The Bridge to `test_agent.py`

Now you have the full mental model:

1. **AI systems are non-deterministic** — same input, different output every time. Traditional `assert` testing breaks down.

2. **Evals replace assertions** — instead of "is the output exactly X?", we ask "how good is the output on dimension Y?" and get a score from 0 to 1.

3. **DeepEval provides the framework** — metrics, test cases (Goldens), instrumentation (tracing), and the evaluation loop.

4. **A Judge LLM does the scoring** — a separate, unbiased model reads the agent's work and grades it.

With this foundation, open `test_agent.py`. You'll see:
- **Two metrics:** `TaskCompletionMetric` (did the agent do the job?) and `ToolCorrectnessMetric` (did it pick the right tool?).
- **Four Goldens:** Four test scenarios, each with an input and expected tools.
- **The evaluation loop:** `evals_iterator` walks through each golden, runs the agent, captures the trace, and lets the judge score it.
- **Cross-vendor setup:** Claude runs the agent, GPT-4o runs the judge.

Everything in `test_agent.py` is a direct application of the concepts from this document. Let's go.

---

## Quick Glossary

| Term | Definition |
|------|-----------|
| **Eval** | A structured process for measuring AI output quality on a specific dimension. Produces a score (0–1), not a pass/fail. |
| **Metric** | A specific evaluation criterion (e.g., AnswerRelevancy, Faithfulness, ToolCorrectness). Each metric measures one quality dimension. |
| **Golden** | A test case — contains the input to send to the agent, plus any expected values (expected output, expected tools) for comparison. |
| **EvaluationDataset** | A collection of Goldens that form one evaluation suite. |
| **Judge LLM** | A separate LLM used to score the agent's outputs. Not the same model being tested. |
| **Threshold** | The minimum score (0–1) for a metric to pass. Set by the test author based on quality requirements. |
| **Trace** | The full record of an agent's execution — every tool call, intermediate step, and final response. Captured by DeepEval's instrumentation. |
| **Non-deterministic** | Producing different outputs for the same input across runs. This is inherent to LLMs and is the reason traditional testing doesn't work. |
| **Cross-vendor** | Using different LLM providers for the agent (e.g., Anthropic's Claude) and the judge (e.g., OpenAI's GPT-4o) to avoid self-evaluation bias. |
| **Instrumentation** | Code added to the agent (like DeepEval's `CallbackHandler` and `@observe`) that captures execution traces without changing the agent's behavior. |
| **DeepEval** | An open-source Python framework for evaluating LLM applications. Provides metrics, tracing, and test infrastructure. |

  
  Tracing = visibility inside the agent's execution

  When your agent runs, it does multiple things internally — an LLM call, then a tool call, then another LLM call. Tracing captures each of those internal
  steps as spans so DeepEval can see what happened at each level, not just the final output.

  ---
  Why safety tests don't need tracing
  
  BiasMetric, ToxicityMetric, PIILeakageMetric only look at the final text output. They don't care how the agent got there — no tools, no intermediate steps.
  Just: "read this response, is it biased?" So no tracing needed.

  ---
  Why the other tests do need tracing
  
  - ToolCorrectnessMetric — needs to know which tools were called during the run. That information lives inside the agent's execution, not in the final output.
   Tracing captures the tool span so DeepEval can read tools_called.
  - TaskCompletionMetric, StepEfficiencyMetric — the judge needs to see the full sequence of steps the agent took, not just the answer.
  - ContextualPrecision/Recall — needs to see which chunks were retrieved inside the RAG pipeline. That's captured as a retrieval span.

  ---
  The one-line version:
  
  ▎ If the metric only reads the final reply → no tracing needed.
  ▎ If the metric needs to look inside the agent's steps → tracing required.

  @observe creates the outer trace, CallbackHandler captures every LangChain span inside it, and update_current_trace is how you explicitly attach
  tools_called, retrieval_context, and expected_tools so the metrics can find them.

- tools_called is hardcoded — you're telling DeepEval "these tools were called", you're not actually running the agent
  - actual_output is hardcoded — you're telling DeepEval "this is what the agent said"
  - No evals_iterator, no @observe, no CallbackHandler — no tracing at all

  DeepEval just takes your word for it and scores against expected_tools.

  ---
  In our test_agent.py the same metric works differently:

  # us — agent runs live, tools captured via tracing
  for golden in dataset.evals_iterator(metrics=[tool_correctness]):
      support_agent(golden.input)   # @observe captures tools_called automatically

  The @observe + CallbackHandler watches the agent run in real time and populates tools_called on the trace. evals_iterator then reads that trace to build the
  LLMTestCase internally — you never write tools_called yourself.

  ---
  So the docs example is essentially the static pattern applied to tool testing — useful if you already have a captured conversation log and want to check if
  the right tools fired. But if you want to test the live agent, tracing is what makes it work without you having to hardcode anything.

---
---

# Wersja polska

> ⬆️ [Back to the English version](#introduction--why-ai-needs-a-completely-different-kind-of-testing)

# Wprowadzenie — dlaczego AI wymaga zupełnie innego rodzaju testowania

> **Przeczytaj to, zanim otworzysz jakikolwiek plik z testami.** Ten dokument stanowi fundament dla wszystkiego, co następuje. Odpowiada na cztery pytania:
> 1. Co dokładnie testujemy, gdy mówimy „testowanie systemu AI"?
> 2. Dlaczego nie możemy go testować tak, jak tradycyjnego oprogramowania?
> 3. Czym są Evals i jak implementuje je DeepEval?
> 4. Czym jest Judge LLM i dlaczego go potrzebujemy?
>
> Gdy oswoisz się z tymi pojęciami, `test_agent.py` (pierwszy plik z testami) stanie się od razu zrozumiały.

---

## 1. Czym dokładnie jest testowanie AI?

Kiedy ktoś mówi „przetestuj aplikację webową", dokładnie wiesz, co to znaczy — kliknąć przycisk, sprawdzić bazę danych, zweryfikować kod odpowiedzi. System jest dobrze zdefiniowany: dane wejściowe wchodzą, przewidywalne dane wyjściowe wychodzą.

Systemy AI są jednak inne. Nie istnieje jeden „kształt" aplikacji AI. W tym kursie mamy do czynienia z czterema różnymi typami systemów AI, a każdy ma własne wyzwania testowe:

### 1.1 Agenci AI

Agent AI to LLM, który potrafi **podejmować akcje** — sam decyduje, które narzędzia wywołać, w jakiej kolejności i z jakimi argumentami, a następnie interpretuje wyniki, aby sformułować końcową odpowiedź.

**Przykład z naszego kodu:** `agent_plain.py` to agent obsługi klienta z dwoma narzędziami — `get_order_status()` i `get_refund_policy()`. Gdy użytkownik pyta „Gdzie jest moje zamówienie ORD-1042?", agent musi:
1. **Zdecydować**, że to pytanie o status zamówienia (a nie o zwroty).
2. **Wybrać** narzędzie `get_order_status`.
3. **Wyciągnąć** identyfikator zamówienia „ORD-1042" z wiadomości użytkownika i przekazać go jako argument.
4. **Zinterpretować** odpowiedź narzędzia i sformułować pomocną odpowiedź.

**Co może pójść nie tak:**
- Agent wywołuje złe narzędzie (pyta o politykę zwrotów, gdy użytkownik chce poznać status zamówienia).
- Agent wywołuje właściwe narzędzie ze złymi argumentami (przekazuje „1042" zamiast „ORD-1042").
- Agent wywołuje właściwe narzędzie, dostaje właściwe dane, ale błędnie je interpretuje lub zniekształca w końcowej odpowiedzi.
- Agent wywołuje niepotrzebne dodatkowe narzędzia, tracąc czas i pieniądze.
- Agent ignoruje instrukcje z system promptu (wychodzi poza markę, daje długie odpowiedzi, mimo że miał być zwięzły).

Każdy z tych rodzajów błędów wymaga innej strategii oceny. Dlatego `test_agent.py` używa **TaskCompletionMetric** (czy całe zadanie zostało wykonane?) oraz **ToolCorrectnessMetric** (czy wybrano właściwe narzędzie?).

### 1.2 Narzędzia MCP (Model Context Protocol)

MCP to protokół, który pozwala agentom AI łączyć się z **zewnętrznymi serwerami narzędzi**. Zamiast definiować narzędzia bezpośrednio w kodzie, agent odkrywa je dynamicznie z serwera MCP w czasie działania.

**Przykład z naszego kodu:** `mcp_server.py` udostępnia przez MCP narzędzie `get_shipping_options`. Agent z instrumentacją w `agent_instrumented.py` łączy się z tym serwerem MCP przy starcie i dodaje narzędzie do wysyłki do swojego zestawu obok zwykłych narzędzi w Pythonie.

**Czym różni się testowanie MCP:**
- Agent nie wywołuje tylko lokalnej funkcji — wywołuje narzędzie odkryte w czasie działania na zewnętrznym serwerze.
- Nazwy i opisy narzędzi pochodzą z serwera MCP, a nie z kodu agenta.
- Agent musi poprawnie rozpoznać, że pytanie użytkownika o wysyłkę należy skierować do narzędzia MCP, a nie do narzędzi zdefiniowanych lokalnie.

W `test_agent.py` czwarty golden testuje dokładnie to — pyta „Jakie opcje wysyłki oferujecie?" i oczekuje, że agent wywoła `get_shipping_options`, czyli narzędzie udostępniane przez MCP. Mechanika testu jest taka sama (ToolCorrectnessMetric nie rozróżnia, czy narzędzie jest lokalne, czy z MCP), ale *powierzchnia integracji* jest szersza.

### 1.3 Chatboty (rozmowy wieloturowe)

Chatbot przechowuje historię rozmowy przez wiele wiadomości użytkownika. W przeciwieństwie do jednoturowego agenta, który przetwarza jedno pytanie w izolacji, chatbot musi pamiętać, co zostało powiedziane wcześniej, i przez całą rozmowę pozostawać w swojej roli.

**Przykład z naszego kodu:** `chatbot.py` to wieloturowy bot wsparcia. Użytkownik może napisać:
- Tura 1: „Mój numer zamówienia to ORD-1042."
- Tura 2: „Czy dotrze na czas?"
- Tura 3: „Jaki był ten termin dostawy, o którym wspomniałeś?"

Chatbot musi przenosić kontekst dalej — musi pamiętać numer zamówienia z tury 1, aby odpowiedzieć w turze 2, oraz termin dostawy podany w turze 2, aby odpowiedzieć w turze 3.

**Co może pójść nie tak:**
- Chatbot zapomina informacje z wcześniejszych tur (błąd pamięci).
- Chatbot wypada z roli — np. bot obsługi klienta zaczyna doradzać w gotowaniu.
- Pojedyncze tury są nie na temat, nawet jeśli cała rozmowa wydaje się rozsądna.
- Rozmowa technicznie postępuje, ale nigdy nie rozwiązuje problemu klienta.

Takie błędy wymagają **metryk konwersacyjnych**: KnowledgeRetention, RoleAdherence, TurnRelevancy i ConversationalGEval — wszystkie opisane w `test_chatbot.py`.

### 1.4 RAG (Retrieval-Augmented Generation)

Agent RAG nie polega na wiedzy z treningu LLM, aby odpowiadać na pytania. Zamiast tego najpierw **wyszukuje** odpowiednie dokumenty w bazie wiedzy, a potem używa ich jako kontekstu do wygenerowania odpowiedzi.

**Przykład z naszego kodu:** `rag_agent.py` ma magazyn wektorowy z 9 dokumentami polityk (wysyłka, zwroty, anulowanie itd.). Gdy użytkownik pyta „Jaka jest polityka zwrotów dla elektroniki?", agent:
1. **Wyszukuje** 3 najbardziej trafne dokumenty polityk z magazynu wektorowego.
2. **Czyta** te dokumenty.
3. **Generuje** odpowiedź na podstawie pobranej treści.

**Co może pójść nie tak — błędy specyficzne dla RAG:**
- **Halucynacja:** Agent mówi coś, czego nie ma w pobranych dokumentach. Z wyszukiwania wynika „15 dni", a agent mówi „30 dni".
- **Zły ranking wyszukiwania:** Najtrafniejszy dokument jest na 3. miejscu, a nieistotne na 1. i 2. LLM może przeoczyć ten ważny.
- **Niepełne wyszukiwanie:** Baza wiedzy zawiera odpowiedź, ale mechanizm wyszukiwania nie wyciągnął właściwego dokumentu.
- **Nietrafna odpowiedź:** Pobrane dokumenty są w porządku, ale agent mimo to odpowiada nie na temat.

Testowanie RAG wymaga wyspecjalizowanego zestawu metryk (Faithfulness, ContextualPrecision, ContextualRecall, AnswerRelevancy) opisanych w `test_rag_agent.py`.

---

## 2. Dlaczego tradycyjne testowanie nie działa

### Problem determinizmu

Tradycyjne testowanie oprogramowania opiera się na jednym fundamentalnym założeniu: **te same dane wejściowe zawsze dają te same dane wyjściowe.**

```
# Tradycyjny test — działa, bo oprogramowanie jest deterministyczne
assert add(2, 3) == 5          # Zawsze prawda. Za każdym razem. Na zawsze.
assert login("admin", "pass123") == "Welcome, admin!"  # Przewidywalne.
```

Piszesz asercję. Uruchamiasz ją 1000 razy. Przechodzi 1000 razy. Jeśli zawiedzie, coś jest zepsute.

Spróbuj teraz tego samego z agentem AI:

```
# Test agenta AI — to NIE działa
response = support_agent("Where is my order ORD-1042?")
assert response == "Order ORD-1042 is Shipped. ETA: 2026-05-13."
```

**Dlaczego to zawodzi:** Uruchom to 10 razy, a możesz dostać 10 nieco różnych odpowiedzi:
- „Order ORD-1042 has been shipped and should arrive by May 13, 2026."
- „Your order ORD-1042 is currently shipped! Expected delivery: 2026-05-13."
- „I checked your order — ORD-1042 is on its way! It's expected to arrive by May 13th."
- „Great news! Order ORD-1042 has shipped. ETA is May 13, 2026."

Wszystkie cztery odpowiedzi są **poprawne**. Wszystkie przekazują tę samą informację. Ale żadna nie pasuje do dokładnego ciągu znaków z asercji. Test zawodzi w 100% przypadków, mimo że agent działa doskonale.

### Dlaczego systemy AI są niedeterministyczne

LLM generują tekst przez **próbkowanie z rozkładów prawdopodobieństwa**.

...Dla tych samych danych wejściowych mogą zwracać różne wyniki. A przy temperature > 0 ta zmienność jest zamierzona i wynika z projektu.

### Pułapka dopasowywania ciągów znaków

Instynkt tradycyjnego testowania każe dopasowywać ciągi znaków:

```
# Wszystkie poniższe to złe pomysły w testowaniu AI:
assert "shipped" in response.lower()        # A co, jeśli napisze "on its way"?
assert response.startswith("Order ORD")     # A co, jeśli napisze "Your order"?
assert len(response) < 100                  # Arbitralne, ignoruje jakość treści
```

Możesz bawić się w „whack-a-mole" z wyrażeniami regularnymi i sprawdzaniem podciągów, ale nigdy nie pokryjesz całej przestrzeni poprawnych odpowiedzi. Więcej czasu spędzisz na utrzymywaniu asercji niż na faktycznym testowaniu agenta.

### Co naprawdę chcemy testować

Pytanie nie brzmi „czy agent wyprodukował dokładnie ten ciąg znaków?" — brzmi:

- **Czy agent podał właściwą informację?** (poprawność semantyczna, a nie dopasowanie ciągów)
- **Czy użył właściwego narzędzia?** (behawioralnie, a nie na podstawie wyniku)
- **Czy odpowiedź była trafna względem pytania?** (ocena semantyczna)
- **Czy przestrzegał swoich instrukcji?** (kontrola zgodności)
- **Czy był efektywny?** (liczenie kroków, a nie sprawdzanie wyniku)
- **Czy halucynował?** (oparcie faktów w źródłach)
- **Czy był bezpieczny, bezstronny i chronił prywatność?** (guardrails)

Na żadne z tych pytań nie da się odpowiedzieć przez `assert response == expected`. Każde wymaga **osądu** — zdolności przeczytania odpowiedzi, zrozumienia jej znaczenia i oceny jej jakości.

Tu wchodzą **Evals**.

---

## 3. Czym są Evals? Jak działa DeepEval?

### Evals — koncepcja

„Eval" to skrót od **evaluation** (ewaluacja). W świecie AI eval to ustrukturyzowany, powtarzalny proces mierzenia, jak dobrze system AI radzi sobie w konkretnym wymiarze jakości.

Pomyśl o tym tak:

| Tradycyjne testowanie | Evals w AI |
|---|---|
| Binarne: przeszedł lub nie | Punktowane: od 0.0 do 1.0 |
| Dokładne dopasowanie | Ocena semantyczna |
| Deterministyczne | Probabilistyczne |
| „Czy wynik jest poprawny?" | „Jak dobry jest wynik?" |
| Pisane przez inżynierów QA | Oceniane przez inny LLM |

Eval nie pyta „czy to jest dokładnie dobrze?" — pyta „jak dobre to jest w skali?", a następnie ustawiasz **próg (threshold)**, który decyduje, co jest wystarczająco dobre.

### DeepEval — framework

DeepEval to open-source'owy framework w Pythonie do oceny aplikacji opartych na LLM. Dostarcza:

1. **Metryki** — gotowe kryteria oceny (AnswerRelevancy, Faithfulness, ToolCorrectness itd.) oraz możliwość definiowania własnych kryteriów przez GEval.
2. **Przypadki testowe** — ustrukturyzowane kontenery na dane wejściowe, wyjściowe i oczekiwane wartości (Golden).
3. **Judge LLM** — LLM, który ocenia wyniki (wyjaśniony w sekcji 4 poniżej).
4. **Tracing/instrumentację** — integracje z LangChain, OpenAI itd., które automatycznie rejestrują, co zrobił agent (wywołania narzędzi, kroki pośrednie, pobrane dokumenty).
5. **Runner testów** — integrację z pytest lub samodzielne metody `evaluate()` / `evals_iterator()`.

### Jak krok po kroku działa ewaluacja w DeepEval

Oto, co się dzieje, gdy uruchamiasz plik testowy taki jak `test_agent.py`:

```
Krok 1: Zdefiniuj dane testowe
    ┌──────────────────────────────────────────────────────┐
    │  Golden(                                             │
    │      input="Where is my order ORD-1042?",            │
    │      expected_tools=[ToolCall(name="get_order_status")]│
    │  )                                                   │
    └──────────────────────────────────────────────────────┘
    „Golden" to jeden scenariusz testowy — dane wejściowe, które
    wyślesz do agenta, plus oczekiwane wartości do porównania.

Krok 2: Wybierz metryki
    ┌──────────────────────────────────────────────────────┐
    │  task_completion  = TaskCompletionMetric(threshold=0.7)│
    │  tool_correctness = ToolCorrectnessMetric()           │
    └──────────────────────────────────────────────────────┘
    Każda metryka potrafi ocenić jeden wymiar jakości.
    Próg (threshold) to TWOJA definicja „wystarczająco dobrego".

Krok 3: Uruchom agenta
    ┌──────────────────────────────────────────────────────┐
    │  support_agent("Where is my order ORD-1042?")        │
    └──────────────────────────────────────────────────────┘
    Agent działa naprawdę — wywołuje narzędzia, generuje
    odpowiedź. Instrumentacja DeepEval rejestruje wszystko
    jako „trace" (sekwencję kroków wykonanych przez agenta).

Krok 4: Judge LLM ocenia trace
    ┌──────────────────────────────────────────────────────┐
    │  Judge (GPT-4o) analizuje:                           │
    │    - dane wejściowe użytkownika                      │
    │    - pełny trace wykonania agenta                    │
    │    - końcową odpowiedź                               │
    │    - oczekiwane wartości z Golden                    │
    │                                                      │
    │  Wystawia wynik: 0.85                                │
    │  Próg wynosił 0.7 → PASS ✓                           │
    └──────────────────────────────────────────────────────┘
```

### Jak działa punktacja

Każda metryka DeepEval zwraca wynik od **0.0 do 1.0**:

| Wynik | Znaczenie |
|-------|-----------|
| 1.0 | Idealnie — wynik w pełni spełnia metrykę |
| 0.7–0.9 | Dobrze — drobne usterki, ale ogólnie solidnie |
| 0.4–0.6 | Średnio — jest duże pole do poprawy |
| 0.1–0.3 | Słabo — wykryto poważne błędy |
| 0.0 | Całkowita porażka w tej metryce |

Dla każdej metryki ustawiasz **próg (threshold)** — to Twoja linia pass/fail. Jeśli wynik jest równy progowi lub wyższy, test przechodzi. Jeśli niższy — test nie przechodzi.

**Próg to decyzja projektowa, a nie reguła.** Różne metryki i różne przypadki użycia uzasadniają różne progi:

- **Metryki jakości** (AnswerRelevancy, TaskCompletion, GEval): zwykle `0.7` — chcesz wysokiej jakości, ale dopuszczasz pewną elastyczność.
- **Metryki bezpieczeństwa** (Bias, Toxicity, PII): w naszych plikach ustawione na `0.5` — te wyniki mogą być zaszumione, ale każdy system produkcyjny powinien ustawiać je wyżej.
- **Metryki efektywności** (StepEfficiency): zwykle `0.5` — agenci rzadko wybierają teoretycznie optymalną ścieżkę, więc dopuszczasz większy luz.

### Dwa typy metryk — deterministyczne vs. oceniane przez LLM

Nie wszystkie metryki używają judge LLM:

**Metryki deterministyczne** liczą wynik ścisłą logiką — bez udziału LLM:
- `ToolCorrectnessMetric` — porównuje faktyczne wywołania narzędzi z oczekiwanymi. To porównanie zbiorów. Agent albo wywołał `get_order_status`, albo nie. Nie trzeba niczego interpretować.

**Metryki oceniane przez LLM** proszą inny LLM o ocenę jakości:
- `TaskCompletionMetric` — nie istnieje wzór na „czy agent ukończył zadanie". Trzeba zrozumieć intencję użytkownika, działania agenta i to, czy wynik ma sens. Ocenić to może tylko LLM.
- `AnswerRelevancyMetric`, `FaithfulnessMetric`, `GEval` i wszystkie metryki bezpieczeństwa — wszystkie wymagają semantycznego rozumienia, które zapewnić może tylko LLM.

---

## 4. Judge LLM — dlaczego drugi LLM ocenia pierwszego

### Główna idea

Skoro nie możemy używać dopasowywania ciągów znaków do oceny wyników AI, a do oceny jakości potrzebujemy rozumienia semantycznego — kto ma oceniać? Odpowiedź: **inny LLM**.

To jest **Judge LLM** (zwany też „modelem oceniającym"). To osobny LLM, którego zadaniem jest przeczytać pracę agenta i ją ocenić.

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│ Użytkownik   │       │   Agent LLM     │       │  Judge LLM  │
│ Pytanie      │──────▶│ (testowany)     │──────▶│ (oceniający)│
│              │       │                 │       │             │
│ „Gdzie jest  │       │  Wywołuje       │       │ Analizuje   │
│  moje        │       │  narzędzia,     │       │ trace i     │
│  zamówienie?"│       │  generuje       │       │ wynik,      │
│              │       │  odpowiedź      │       │ wystawia    │
│              │       │                 │       │ ocenę       │
└─────────────┘       └─────────────────┘       └─────────────┘
                                                       │
                                                  Wynik: 0.85
                                                  PASS ✓
```

### Dlaczego nie pozwolić agentowi oceniać samego siebie?

Używanie tego samego LLM do generowania i oceniania tworzy konflikt interesów — jak ocenianie własnego egzaminu. Badania pokazują, że LLM mają tendencję do oceniania własnych wyników łaskawiej niż wyników innych modeli. Nazywa się to **self-evaluation bias** (błąd samooceny).

### Konfiguracja cross-vendor — nasze podejście

W naszych plikach testowych celowo używamy **różnych dostawców** dla agenta i dla sędziego:

| Rola | Model | Dostawca | Cel |
|------|-------|----------|-----|
| Agent LLM (system testowany) | Claude / GPT-4o | Anthropic / OpenAI | Uruchamia agenta, generuje odpowiedzi |
| Judge LLM (oceniający) | GPT-4o | OpenAI | Ocenia działanie agenta |

Taka konfiguracja cross-vendor oznacza, że:
- Agent (uczeń) i sędzia (nauczyciel) pochodzą z różnych „rodzin".
- Sędzia nie jest stronniczy wobec wyników agenta.
- Ocena jest bardziej obiektywna i wiarygodna.

### Co właściwie robi sędzia

Gdy uruchamia się metryka taka jak `TaskCompletionMetric`, wewnętrznie dzieje się to:

1. DeepEval buduje **prompt oceniający** — starannie zaprojektowany prompt, który mówi judge LLM dokładnie, co i jak ocenić.
2. Prompt zawiera dane wejściowe użytkownika, pełny trace agenta (wywołania narzędzi, kroki pośrednie, końcową odpowiedź) oraz kryteria oceny.
3. Judge LLM czyta wszystko i zwraca:
   - **Wynik** (od 0.0 do 1.0)
   - **Uzasadnienie** (tekstowe wyjaśnienie, dlaczego wystawił taki wynik)
4. DeepEval porównuje wynik z progiem i raportuje pass/fail.

Prompty oceniające zostały zaprojektowane przez autorów DeepEval z użyciem najlepszych praktyk prompt engineeringu — nie piszesz ich samodzielnie. Każda metryka ma własny szablon promptu oceniającego, zoptymalizowany pod konkretny wymiar jakości.

### Sędzia nie jest idealny — i to w porządku

Judge LLM to też AI, więc również jest niedeterministyczny. Ten sam wynik agenta może dostać 0.78 w jednym uruchomieniu i 0.82 w następnym. Dlatego:

- **Progi powinny mieć margines.** Jeśli Twoja rzeczywista minimalna akceptowalna jakość to 0.8, ustaw próg na 0.7, aby pochłonąć rozrzut ocen.
- **Uruchamiaj evals wielokrotnie**, gdy wyniki są graniczne.
- **Patrz na uzasadnienia**, nie tylko na wyniki. Metryki DeepEval często podają tekstowe wyjaśnienie wyniku — jest ono bardziej informatywne niż sama liczba.

---

## 5. Podsumowanie — pomost do `test_agent.py`

Masz już pełny model mentalny:

1. **Systemy AI są niedeterministyczne** — te same dane wejściowe, za każdym razem inny wynik. Tradycyjne testowanie przez `assert` się załamuje.

2. **Evals zastępują asercje** — zamiast „czy wynik to dokładnie X?" pytamy „jak dobry jest wynik w wymiarze Y?" i dostajemy wynik od 0 do 1.

3. **DeepEval dostarcza framework** — metryki, przypadki testowe (Golden), instrumentację (tracing) i pętlę ewaluacji.

4. **Punktację robi Judge LLM** — osobny, bezstronny model czyta pracę agenta i ją ocenia.

Mając ten fundament, otwórz `test_agent.py`. Zobaczysz:
- **Dwie metryki:** `TaskCompletionMetric` (czy agent wykonał zadanie?) i `ToolCorrectnessMetric` (czy wybrał właściwe narzędzie?).
- **Cztery Golden:** cztery scenariusze testowe, każdy z danymi wejściowymi i oczekiwanymi narzędziami.
- **Pętlę ewaluacji:** `evals_iterator` przechodzi przez każdy golden, uruchamia agenta, rejestruje trace i pozwala sędziemu go ocenić.
- **Konfigurację cross-vendor:** Claude uruchamia agenta, GPT-4o uruchamia sędziego.

Wszystko w `test_agent.py` jest bezpośrednim zastosowaniem pojęć z tego dokumentu. Zaczynamy.

---

## Krótki słowniczek

| Termin | Definicja |
|--------|-----------|
| **Eval** | Ustrukturyzowany proces mierzenia jakości wyniku AI w konkretnym wymiarze. Zwraca wynik (0–1), a nie pass/fail. |
| **Metric (metryka)** | Konkretne kryterium oceny (np. AnswerRelevancy, Faithfulness, ToolCorrectness). Każda metryka mierzy jeden wymiar jakości. |
| **Golden** | Przypadek testowy — zawiera dane wejściowe do wysłania agentowi oraz oczekiwane wartości (oczekiwany wynik, oczekiwane narzędzia) do porównania. |
| **EvaluationDataset** | Zbiór Golden tworzący jeden zestaw ewaluacyjny. |
| **Judge LLM** | Osobny LLM używany do oceniania wyników agenta. To nie ten sam model, który jest testowany. |
| **Threshold (próg)** | Minimalny wynik (0–1), przy którym metryka przechodzi. Ustawiany przez autora testu na podstawie wymagań jakościowych. |
| **Trace** | Pełny zapis wykonania agenta — każde wywołanie narzędzia, krok pośredni i końcowa odpowiedź. Rejestrowany przez instrumentację DeepEval. |
| **Niedeterministyczny** | Zwracający różne wyniki dla tych samych danych wejściowych w kolejnych uruchomieniach. Jest to cecha LLM i powód, dla którego tradycyjne testowanie nie działa. |
| **Cross-vendor** | Używanie różnych dostawców LLM dla agenta (np. Claude od Anthropic) i dla sędziego (np. GPT-4o od OpenAI), aby uniknąć błędu samooceny. |
| **Instrumentation (instrumentacja)** | Kod dodany do agenta (jak `CallbackHandler` i `@observe` z DeepEval), który rejestruje trace wykonania bez zmieniania zachowania agenta. |
| **DeepEval** | Open-source'owy framework w Pythonie do oceny aplikacji LLM. Dostarcza metryki, tracing i infrastrukturę testową. |

  
  Tracing = wgląd w wykonanie agenta

  Gdy agent działa, wewnętrznie robi wiele rzeczy — wywołanie LLM, potem wywołanie narzędzia, potem kolejne wywołanie LLM. Tracing rejestruje każdy z tych
  wewnętrznych kroków jako spany, dzięki czemu DeepEval widzi, co się działo na każdym poziomie, a nie tylko końcowy wynik.

  ---
  Dlaczego testy bezpieczeństwa nie potrzebują tracingu

  BiasMetric, ToxicityMetric, PIILeakageMetric patrzą tylko na końcowy tekst wyjściowy. Nie obchodzi ich, jak agent do niego doszedł — bez narzędzi, bez kroków
  pośrednich. Tylko: „przeczytaj tę odpowiedź, czy jest stronnicza?". Tracing nie jest więc potrzebny.

  ---
  Dlaczego pozostałe testy potrzebują tracingu

  - ToolCorrectnessMetric — musi wiedzieć, które narzędzia zostały wywołane podczas działania. Ta informacja znajduje się wewnątrz wykonania agenta, a nie
   w końcowym wyniku. Tracing rejestruje span narzędzia, żeby DeepEval mógł odczytać tools_called.
  - TaskCompletionMetric, StepEfficiencyMetric — sędzia musi zobaczyć pełną sekwencję kroków agenta, a nie tylko odpowiedź.
  - ContextualPrecision/Recall — musi zobaczyć, które fragmenty zostały pobrane wewnątrz pipeline'u RAG. Jest to rejestrowane jako span retrieval.

  ---
  Wersja w jednym zdaniu:

  ▎ Jeśli metryka czyta tylko końcową odpowiedź → tracing niepotrzebny.
  ▎ Jeśli metryka musi zajrzeć do kroków agenta → tracing jest wymagany.

  @observe tworzy zewnętrzny trace, CallbackHandler rejestruje każdy span LangChain wewnątrz niego, a update_current_trace to sposób na jawne dołączenie
  tools_called, retrieval_context i expected_tools, aby metryki mogły je znaleźć.

- tools_called jest zakodowane na sztywno — mówisz DeepEval „te narzędzia zostały wywołane", nie uruchamiasz faktycznie agenta
  - actual_output jest zakodowane na sztywno — mówisz DeepEval „tak odpowiedział agent"
  - Brak evals_iterator, brak @observe, brak CallbackHandler — w ogóle brak tracingu

  DeepEval po prostu wierzy Ci na słowo i ocenia względem expected_tools.

  ---
  W naszym test_agent.py ta sama metryka działa inaczej:

  # my — agent działa na żywo, narzędzia rejestrowane przez tracing
  for golden in dataset.evals_iterator(metrics=[tool_correctness]):
      support_agent(golden.input)   # @observe automatycznie rejestruje tools_called

  @observe + CallbackHandler obserwują agenta w czasie rzeczywistym i uzupełniają tools_called w trace. evals_iterator odczytuje ten trace, aby wewnętrznie
  zbudować LLMTestCase — nigdy sam nie piszesz tools_called.

  ---
  Przykład z dokumentacji to więc w zasadzie wzorzec statyczny zastosowany do testowania narzędzi — przydatny, jeśli masz już zarejestrowany log rozmowy i chcesz
  sprawdzić, czy uruchomiły się właściwe narzędzia. Ale jeśli chcesz testować agenta na żywo, to tracing sprawia, że działa to bez konieczności zakodowywania czegokolwiek na sztywno.
To capture live tools_called and actual_output from a real agent, you should instrument your agent with the @observe decorator and use update_current_span / update_current_trace to record the data as it flows through your app. Then drive evaluation with EvaluationDataset and evals_iterator().