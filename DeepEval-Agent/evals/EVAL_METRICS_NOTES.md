METRIC 1: TaskCompletionMetric

Category: Agentic / Trace-Level

What is measures: 
TaskCompletionMetric evaluates whether the AI Agent successfully completed the task the user asked it to do, end to end. It looks at the full trace of the agent's execution - the input, the tools it called, the intermediate results, and the final response - and judges whether the overall outcome satisfies the user's request.

Why it matters: 
An Agent might call the right tool but still fail the task (e.g, it looks up the order but gives the user incorrect information). Or it might call the wrong tool but still stumble into a helpful answer. TaskCompletion captures the holistic outcome - did the user walk away with what they needed?

METRIC 2: ToolCorrectnessMetric

Category: Agentic / Tool Calls

What is measures:
ToolCorrectnessMetric compares the tools the Agent actually called with the expected tools defined for the test. In the tested default configuration, it checks tool names against the expected list.

Why it matters:
An Agent can produce a plausible answer without using the right tool (e.g, it answers an order status question without calling get_order_status). ToolCorrectness checks whether the Agent used the expected tools, rather than judging the final answer alone.


METRIC 3: PromptAlignmentMetric

Category: Agentic / Instruction Following

What is measures:
PromptAlignmentMetric evaluates whether the Agent's final response follows the specified prompt instructions. In this test, those instructions ask the Agent to be friendly, use available tools for order and refund questions, and keep replies short and helpful.

Why it matters:
An Agent might provide a useful answer but ignore instructions about its tone or length. PromptAlignment checks whether the response respects those instructions; it does not by itself establish that the answer is correct or that a particular tool was called.
