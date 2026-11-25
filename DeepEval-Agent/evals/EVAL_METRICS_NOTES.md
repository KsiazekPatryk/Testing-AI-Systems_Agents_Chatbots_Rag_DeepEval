METRIC 1: TaskCompletionMetric

Category: Agentic / Trace-Level

What is measures: 
TaskCompletionMetric evaluates whether the AI Agent successfully completed the task the user asked it to do, end to end. It looks at the full trace of the agent's execution - the input, the tools it called, the intermediate results, and the final response - and judges whether the overall outcome satisfies the user's request.

Why it matters: 
An Agent might call the right tool but still fail the task (e.g, it looks up the order but gives the user incorrect information). Or it might call the wrong tool but still stumble into a helpful answer. TaskCompletion captures the holistic outcome - did the user walk away with what they needed?


