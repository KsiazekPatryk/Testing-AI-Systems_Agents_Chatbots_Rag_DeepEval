from deepeval.test_case import LLMTestCase
from deepeval import evaluate
from agent_instrumented import support_agent
import deepeval.metrics as TaskCompletionMetric

actual_output = support_agent("Where is my ordder ORD-1042?")

test_case = LLMTestCase(
    input = "Where is my order ORD-1042?",
    actual_output = actual_output
)

evaluate(test_cases = [test_case],
         metrics = [TaskCompletionMetric.TaskCompletionMetric(threshold=0.7, model="claude-sonnet-4-6")])