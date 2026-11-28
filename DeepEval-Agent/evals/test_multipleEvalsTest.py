import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deepeval.metrics import PromptAlignmentMetric
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.tracing import observe
from deepeval.tracing.context import update_current_trace
from deepeval.contextvars import get_current_golden
from agent_instrumented import support_agent as _support_agent
from agent_instrumented import support_agent

@observe(name="support_agent")
def support_agent(user_input: str) -> str:
    return _support_agent(user_input)


prompt_alignment_metric = PromptAlignmentMetric(
    prompt_instructions= [
          "You are a friendly customer-support agent. "
          "Use the available tools to answer order and refund questions. "
          "Keep replies short and helpful."
    ], threshold=0.7, model = "gpt-4o"
)

dataset = EvaluationDataset(goldens = [
    Golden(input = "Where is my order ORD-1042?", multimodal=False),
    Golden(input = "What's the refund policy for electronics?", multimodal=False),
    Golden(input = "I want to return order ORD-2099, what should I do?", multimodal=False)
])

for golden in dataset.evals_iterator (metrics = [prompt_alignment_metric]) :
    support_agent(golden.input)
