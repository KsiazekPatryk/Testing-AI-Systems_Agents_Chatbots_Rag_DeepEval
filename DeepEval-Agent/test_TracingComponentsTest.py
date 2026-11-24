from deepeval.dataset import EvaluationDataset
from deepeval.metrics import TaskCompletionMetric, ToolCorrectnessMetric

task_completion = TaskCompletionMetric(threshold=0.7, model= "gpt-4o")
tool_correctness = ToolCorrectnessMetric()

dataset = EvaluationDataset()
dataset.evals_iterator(metrics = [task_completion, tool_correctness])