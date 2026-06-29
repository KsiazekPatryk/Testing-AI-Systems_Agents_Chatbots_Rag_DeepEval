from deepeval.test_case import LLMTestCase
from agent_instrumented import support_agent

support_agent("Where is my ordder ORD-1042?")

LLMTestCase(
    input = "Where is my order ORD-1042?",
    actual_output = ""
)