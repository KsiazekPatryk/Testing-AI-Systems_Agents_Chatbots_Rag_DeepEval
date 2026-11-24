# DeepEval Agentic Testing Demo

> 🇵🇱 **[Polska wersja tego dokumentu → poniżej](#wersja-polska)** · Wprowadzenie: [INTRO_WHY_AI_EVALS.md](./evals/INTRO_WHY_AI_EVALS.md)

A minimal teaching repo that shows how to evaluate a LangChain agent with
DeepEval's component-level evaluation: **Task Completion** and **Tool
Correctness** metrics, applied to a cross-vendor setup (Claude as the
agent, GPT-4o as the judge).

---

## Files in this repo

| File | Who writes it (in real life) | What it does |
|---|---|---|
| `agent_plain.py` | Developer (before evals exist) | A normal LangChain + Claude agent. No DeepEval code anywhere. |
| `agent_instrumented.py` | Developer (after QA asks) | The **same** agent, with **4 lines added** to make it observable to DeepEval. |
| `test_agent.py` | QA / Tester (you) | Imports the agent, defines goldens, runs metrics. |

---

## The teaching point

The diff between `agent_plain.py` and `agent_instrumented.py` is **4 lines**.
That's the entire ask QA makes of dev:

1. `from deepeval.integrations.langchain import CallbackHandler`
2. `deepeval_callback = CallbackHandler()`
3. `config={"callbacks": [deepeval_callback]}` on `.invoke()`
4. `@observe(name="support_agent")` on the outer wrapper function

Everything else stays exactly the same.

Show students both files side by side. Once they see the diff is tiny,
they stop being intimidated by component-level evaluation.

---

## How to run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your API keys
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...

# 3. (Optional but recommended) log in to Confident AI to see traces in a UI
deepeval login

# 4. Sanity check: run the agent on its own
python agent_instrumented.py

# 5. Run the evaluation
python test_agent.py
```

---

## What you'll see when you run `test_agent.py`

DeepEval will:
1. Invoke `support_agent(...)` for each golden input
2. Capture the full trace (LangChain LLM call + tool call + final message)
3. Apply **Task Completion** to the whole trace
4. Apply **Tool Correctness** to the tool-call span
5. Print scores + reasons per golden

The third golden is intentionally borderline — watch for the interesting
case where Task Completion may pass but Tool Correctness fails (or vice
versa). That's the moment that makes component-level evaluation click.

---

## Suggested lesson flow

| Minute | Activity |
|---|---|
| 0–5 | Show `agent_plain.py`. Ask: "How would you test this?" |
| 5–10 | Show `agent_instrumented.py` side-by-side. Walk through the 4-line diff. |
| 10–25 | Walk through `test_agent.py` line by line. |
| 25–35 | Run it live. Discuss the borderline result. |
| 35+ | Open discussion: what other metrics? what other goldens? |

---

## Reality checks before teaching

DeepEval's integration surface evolves. Before your first session, run the
demo end-to-end once and confirm:

- `ChatAnthropic(model="claude-sonnet-4-5")` — if this errors, swap to the
  latest Claude model from the Anthropic console.
- `from deepeval.integrations.langchain import CallbackHandler` — works as
  written in recent DeepEval versions; older versions may use a different
  import path.
- `Golden(expected_tools=[ToolCall(name="...")])` — accepted in current
  DeepEval; in older versions you may need to pass via `additional_metadata`
  and unpack via `update_current_span`.

Fix any version issue once, then it's solid for the whole course.

---
---

# Wersja polska

> ⬆️ [Back to the English version](#deepeval-agentic-testing-demo)

# DeepEval Agentic Testing Demo — demo testowania agentów

Minimalne repozytorium edukacyjne pokazujące, jak ocenić agenta LangChain
za pomocą ewaluacji na poziomie komponentów w DeepEval: metryki **Task
Completion** i **Tool Correctness**, zastosowane w konfiguracji cross-vendor
(Claude jako agent, GPT-4o jako sędzia).

---

## Pliki w tym repozytorium

| Plik | Kto go pisze (w prawdziwym życiu) | Co robi |
|---|---|---|
| `agent_plain.py` | Developer (zanim pojawią się evals) | Zwykły agent LangChain + Claude. Zero kodu DeepEval. |
| `agent_instrumented.py` | Developer (po prośbie QA) | **Ten sam** agent, z **4 dodanymi liniami**, które czynią go obserwowalnym dla DeepEval. |
| `test_agent.py` | QA / Tester (Ty) | Importuje agenta, definiuje goldeny, uruchamia metryki. |

---

## Najważniejsza lekcja

Różnica między `agent_plain.py` a `agent_instrumented.py` to **4 linie**.
To cała prośba, jaką QA kieruje do developerów:

1. `from deepeval.integrations.langchain import CallbackHandler`
2. `deepeval_callback = CallbackHandler()`
3. `config={"callbacks": [deepeval_callback]}` w `.invoke()`
4. `@observe(name="support_agent")` na zewnętrznej funkcji opakowującej

Cała reszta pozostaje dokładnie taka sama.

Pokaż uczestnikom oba pliki obok siebie. Gdy zobaczą, że różnica jest
niewielka, przestają bać się ewaluacji na poziomie komponentów.

---

## Jak uruchomić

```bash
# 1. Zainstaluj zależności
pip install -r requirements.txt

# 2. Ustaw klucze API
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...

# 3. (Opcjonalnie, ale zalecane) zaloguj się do Confident AI, aby oglądać trace w interfejsie
deepeval login

# 4. Test poprawności: uruchom samego agenta
python agent_instrumented.py

# 5. Uruchom ewaluację
python test_agent.py
```

---

## Co zobaczysz po uruchomieniu `test_agent.py`

DeepEval wykona następujące kroki:
1. Wywoła `support_agent(...)` dla każdego wejścia golden
2. Zarejestruje pełny trace (wywołanie LLM w LangChain + wywołanie narzędzia + końcowa wiadomość)
3. Zastosuje **Task Completion** do całego trace
4. Zastosuje **Tool Correctness** do spana wywołania narzędzia
5. Wypisze wyniki + uzasadnienia dla każdego golden

Trzeci golden jest celowo graniczny — zwróć uwagę na ciekawy przypadek,
w którym Task Completion może przejść, a Tool Correctness nie (lub odwrotnie).
To moment, w którym ewaluacja na poziomie komponentów „klika".

---

## Proponowany przebieg lekcji

| Minuta | Aktywność |
|---|---|
| 0–5 | Pokaż `agent_plain.py`. Zapytaj: „Jak byś to przetestował?" |
| 5–10 | Pokaż `agent_instrumented.py` obok. Omów różnicę 4 linii. |
| 10–25 | Przejdź przez `test_agent.py` linia po linii. |
| 25–35 | Uruchom na żywo. Omów wynik graniczny. |
| 35+ | Otwarta dyskusja: jakie inne metryki? jakie inne goldeny? |

---

## Sprawdzenie rzeczywistości przed prowadzeniem zajęć

Powierzchnia integracji DeepEval ewoluuje. Przed pierwszą sesją uruchom
demo od początku do końca i potwierdź, że:

- `ChatAnthropic(model="claude-sonnet-4-5")` — jeśli zgłasza błąd, zmień na
  najnowszy model Claude z konsoli Anthropic.
- `from deepeval.integrations.langchain import CallbackHandler` — działa tak,
  jak zapisano, w nowszych wersjach DeepEval; starsze wersje mogą używać innej
  ścieżki importu.
- `Golden(expected_tools=[ToolCall(name="...")])` — akceptowane w aktualnej
  wersji DeepEval; w starszych wersjach może być konieczne przekazanie przez
  `additional_metadata` i odczyt przez `update_current_span`.

Napraw problem z wersjami raz, a potem będzie działać stabilnie przez cały kurs.
