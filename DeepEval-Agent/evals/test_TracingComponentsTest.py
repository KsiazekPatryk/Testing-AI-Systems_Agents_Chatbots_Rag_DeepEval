import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deepeval.dataset import EvaluationDataset, Golden
from deepeval.metrics import TaskCompletionMetric, ToolCorrectnessMetric
from deepeval.test_case import ToolCall
from deepeval.tracing import observe
from deepeval.tracing.context import update_current_trace
from deepeval.contextvars import get_current_golden
from agent_instrumented import support_agent as _support_agent


#Trace have expected values and actual values
@observe(name="support_agent")
def support_agent(user_input: str) -> str:
    golden = get_current_golden()
    if golden:
        if golden.expected_tools:
            update_current_trace(expected_tools=golden.expected_tools)

    return _support_agent(user_input)


task_completion = TaskCompletionMetric(threshold=0.7, model= "gpt-4o")
tool_correctness = ToolCorrectnessMetric()


dataset = EvaluationDataset(goldens=[
    Golden(input="Where is my order ORD-1042?", multimodal=False, expected_tools=[ToolCall(name="get_order_status", input_parameters={"order_id": "ORD-1042"})]),

    Golden(input="What is refund policy for electronics?", multimodal=False, expected_tools=[ToolCall(name="get_refund_policy", input_parameters={"category": "electronics"})]),
    ])


for golden in dataset.evals_iterator(metrics = [task_completion, tool_correctness]):
    support_agent(golden.input)