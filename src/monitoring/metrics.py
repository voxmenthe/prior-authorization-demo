class MetricsClient:
    def gauge(self, metric_name: str, value: float):
        print(f"METRIC: {metric_name} = {value}")

    def increment(self, metric_name: str):
        print(f"METRIC: {metric_name} += 1")

class TreeGenerationMetrics:
    def __init__(self):
        self.metrics_client = MetricsClient()
        
    def track_generation(self, tree: dict, generation_time: float):
        self.metrics_client.gauge("tree_generation.duration", generation_time)
        self.metrics_client.increment("tree_generation.count")
        self.metrics_client.gauge("tree_generation.node_count", len(tree.get("nodes", [])))
        self.metrics_client.gauge("tree_generation.depth", self._calculate_depth(tree))

    def _calculate_depth(self, tree: dict) -> int:
        # Placeholder for calculating tree depth
        return 0
        
    def track_llm_usage(self, prompt_tokens: int, completion_tokens: int):
        self.metrics_client.gauge("llm.prompt_tokens", prompt_tokens)
        self.metrics_client.gauge("llm.completion_tokens", completion_tokens)
        self.metrics_client.increment("llm.api_calls")
