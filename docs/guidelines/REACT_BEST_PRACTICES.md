# ReAct Orchestration Best Practices (2025)

**Last Updated:** October 2025
**Status:** Production Ready
**Target:** Ollama local LLM deployments

---

## Overview

This guide provides best practices for implementing and deploying ReAct (Reasoning + Acting) orchestration for tool calling with Ollama models in OpenFatture. ReAct enables local LLMs without native function calling to use the same tools as cloud providers (OpenAI, Anthropic).

**Key Benefits:**
- ✅ Local inference (no API costs, privacy-preserving)
- ✅ Same tool ecosystem as cloud providers
- ✅ 80%+ success rate with proper configuration
- ✅ Full observability with metrics tracking

**Files:**
- `openfatture/ai/orchestration/react.py` - ReActOrchestrator implementation
- `openfatture/ai/orchestration/parsers.py` - ToolCallParser with XML support
- `openfatture/ai/orchestration/states.py` - State management
- `tests/ai/test_react_e2e_ollama.py` - E2E validation tests

---

## 1. Configuration Best Practices

### 1.1 Temperature Settings

**CRITICAL:** Always use `temperature=0.0` for tool calling.

```bash
# .env configuration
OPENFATTURE_AI_PROVIDER=ollama
OPENFATTURE_AI_OLLAMA_MODEL=qwen3:8b
OPENFATTURE_AI_TEMPERATURE=0.0  # MUST be 0.0 for tool calling
OPENFATTURE_AI_OLLAMA_BASE_URL=http://localhost:11434
```

**Why temperature=0.0?**
- Deterministic output ensures consistent tool call format
- Reduces hallucination of tool names/parameters
- Critical for XML tag structure reliability
- Improves parser success rate from ~60% to 80%+

**Testing Temperature Impact:**
```python
# Test with different temperatures
from openfatture.ai.providers.ollama import OllamaProvider

# ❌ BAD: Non-deterministic, inconsistent format
provider_bad = OllamaProvider(model="qwen3:8b", temperature=0.7)

# ✅ GOOD: Deterministic, consistent tool calls
provider_good = OllamaProvider(model="qwen3:8b", temperature=0.0)
```

### 1.2 Model Selection

**Recommended Models (October 2025):**

| Model | Size | Success Rate | Speed | Best For |
|-------|------|--------------|-------|----------|
| **qwen3:8b** (Recommended) | 5.2 GB | 80%+ | Fast | Production tool calling |
| mistral-small3.1 | 15 GB | 85%+ | Medium | Complex reasoning |
| llama3.2 | 7 GB | 70%+ | Fast | General use |
| phi3:medium | 4.2 GB | 65%+ | Very Fast | Simple queries |

**Installation:**
```bash
# Install recommended model
ollama pull qwen3:8b

# Verify installation
ollama list | grep qwen3
```

**Model Testing:**
```python
# Test model before production use
from openfatture.ai.providers.ollama import OllamaProvider

provider = OllamaProvider(model="qwen3:8b", temperature=0.0)

# Health check
assert await provider.health_check()

# List available models
models = await provider.list_models()
assert "qwen3:8b" in models
```

### 1.3 Max Iterations

Set `max_iterations` based on query complexity:

```python
# Simple queries (single tool call)
orchestrator_simple = ReActOrchestrator(
    provider=provider,
    tool_registry=registry,
    max_iterations=5,  # Typical: 2-3 iterations
)

# Complex queries (multi-step reasoning)
orchestrator_complex = ReActOrchestrator(
    provider=provider,
    tool_registry=registry,
    max_iterations=10,  # Allow more steps
)

# Production safety (prevent runaway loops)
orchestrator_prod = ReActOrchestrator(
    provider=provider,
    tool_registry=registry,
    max_iterations=8,  # Balance between capability and safety
)
```

**Guidelines:**
- **5 iterations**: Simple queries (e.g., "How many invoices?")
- **8 iterations**: Standard production setting
- **10+ iterations**: Complex multi-step workflows
- **Monitor**: Track `metrics["max_iterations_reached"]` - should be <5%

---

## 2. Prompt Engineering

### 2.1 XML Format (2025 Standard)

**Always use XML tags for tool calls:**

```xml
<thought>I need to retrieve invoice statistics for 2025</thought>
<action>get_invoice_stats</action>
<action_input>{"year": 2025}</action_input>
```

**Why XML over text format?**
- More robust parsing (less ambiguity)
- Better handling of multiline content
- qwen3:8b naturally generates XML 60%+ of time
- Fallback to legacy text format if needed

### 2.2 System Prompt Guidelines

**Include in system prompt:**
1. **Clear format instructions** with XML examples
2. **Available tools** with descriptions
3. **Parameter schemas** with types and requirements
4. **Few-shot examples** showing successful tool calls
5. **Error handling** guidance

**Example system prompt structure:**
```python
system_prompt = f"""
You are an AI assistant with access to these tools:

{tool_descriptions}

ALWAYS use this XML format for tool calls:

<thought>Your reasoning about what to do</thought>
<action>tool_name</action>
<action_input>{{"param": "value"}}</action_input>

When you have the final answer:

<thought>I have all the information needed</thought>
<final_answer>Your response to the user</final_answer>

Examples:
{few_shot_examples}

IMPORTANT:
- Use valid JSON in <action_input>
- Only call tools that exist
- Provide clear thoughts
- Return final_answer when done
"""
```

### 2.3 Few-Shot Examples

**Include 2-3 examples per tool:**

```yaml
# In prompt template
few_shot_examples:
  - user: "Quante fatture ho emesso?"
    thought: "Devo ottenere le statistiche delle fatture"
    action: "get_invoice_stats"
    action_input: '{"year": 2025}'
    observation: "totale_fatture: 42, importo_totale: 15000.0"
    final_answer: "Hai emesso 42 fatture per un totale di €15.000,00"

  - user: "Mostra le ultime 3 fatture"
    thought: "Devo cercare le fatture più recenti"
    action: "search_invoices"
    action_input: '{"limit": 3}'
    observation: "Found 3 invoices: [...]"
    final_answer: "Ecco le ultime 3 fatture: ..."
```

---

## 3. Error Handling

### 3.1 Tool Execution Errors

**Always handle tool failures gracefully:**

```python
try:
    result = await tool_registry.execute_tool(
        tool_name=parsed.tool_call.tool_name,
        parameters=parsed.tool_call.parameters,
    )

    if result.success:
        observation = format_observation(result.data)
        metrics["tool_calls_succeeded"] += 1
    else:
        # Tool execution failed - provide helpful error
        observation = f"Error: {result.error}. Please try a different approach."
        metrics["tool_calls_failed"] += 1

except ToolNotFoundException:
    # Tool doesn't exist - guide LLM to valid tools
    observation = f"Tool '{tool_name}' not found. Available tools: {available_tools}"

except ValidationError as e:
    # Invalid parameters - help LLM fix them
    observation = f"Invalid parameters: {e}. Expected schema: {tool_schema}"

except Exception as e:
    # Unexpected error - log and continue
    logger.error("tool_execution_failed", tool=tool_name, error=str(e))
    observation = f"Tool execution error: {str(e)}"
```

### 3.2 Parsing Errors

**Multi-strategy parsing with fallback:**

```python
def parse(self, response_text: str) -> ParsedResponse:
    """Parse with multiple strategies."""

    # Strategy 1: Try XML parsing (primary)
    try:
        if xml_result := self._try_parse_xml(response_text):
            self.metrics["xml_parse_count"] += 1
            return xml_result
    except Exception as e:
        logger.debug("xml_parse_failed", error=str(e))

    # Strategy 2: Try legacy text format (fallback)
    try:
        if legacy_result := self._try_parse_legacy(response_text):
            self.metrics["legacy_parse_count"] += 1
            return legacy_result
    except Exception as e:
        logger.debug("legacy_parse_failed", error=str(e))

    # Strategy 3: Treat as final answer (safety)
    logger.warning("no_format_detected", treating_as_final=True)
    return ParsedResponse(is_final=True, content=response_text)
```

### 3.3 Max Iterations Reached

**Provide helpful message when loop limit reached:**

```python
if iteration >= max_iterations:
    self.metrics["max_iterations_reached"] += 1

    # Log detailed state for debugging
    logger.warning(
        "max_iterations_reached",
        iterations=iteration,
        last_tool=last_tool_called,
        conversation_length=len(conversation_messages),
    )

    # Return helpful message to user
    return (
        "Unable to complete your request within the iteration limit. "
        "This usually means the query is too complex. "
        "Please try breaking it into smaller questions."
    )
```

---

## 4. Performance Optimization

### 4.1 Metrics Tracking

**Track key performance metrics:**

```python
# In ReActOrchestrator
self.metrics = {
    "total_executions": 0,          # Total execute() calls
    "tool_calls_attempted": 0,      # Tools attempted
    "tool_calls_succeeded": 0,      # Successful tool calls
    "tool_calls_failed": 0,         # Failed tool calls
    "max_iterations_reached": 0,    # Hit iteration limit
    "total_iterations": 0,          # Sum of all iterations
}

# Get derived metrics
def get_metrics(self) -> dict:
    success_rate = (
        self.metrics["tool_calls_succeeded"] /
        max(1, self.metrics["tool_calls_attempted"])
    )

    avg_iterations = (
        self.metrics["total_iterations"] /
        max(1, self.metrics["total_executions"])
    )

    return {
        **self.metrics,
        "tool_call_success_rate": success_rate,
        "avg_iterations": avg_iterations,
        "parser_stats": self.parser.get_stats(),
    }
```

**Monitor these thresholds:**
- `tool_call_success_rate` ≥ 0.80 (80%)
- `xml_parse_rate` ≥ 0.60 (60%)
- `avg_iterations` ≤ 3.0
- `max_iterations_reached_rate` ≤ 0.05 (5%)

### 4.2 Caching Tool Results

**Cache frequently accessed data:**

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache invoice stats for 1 hour
@lru_cache(maxsize=128)
def get_invoice_stats_cached(year: int, cache_key: str) -> dict:
    """Cached version of get_invoice_stats."""
    return get_invoice_stats(year)

# Generate cache key based on time
def get_cache_key() -> str:
    """Cache key that changes every hour."""
    now = datetime.now()
    return f"{now.year}-{now.month}-{now.day}-{now.hour}"

# Use in tool
def get_invoice_stats(year: int = 2025) -> dict:
    cache_key = get_cache_key()
    return get_invoice_stats_cached(year, cache_key)
```

### 4.3 Parallel Tool Execution (Future)

**For independent tools, execute in parallel:**

```python
# TODO: Implement parallel execution for independent tools
async def execute_tools_parallel(tool_calls: list[ToolCall]) -> list[ToolResult]:
    """Execute multiple independent tools in parallel."""
    tasks = [
        tool_registry.execute_tool(tc.tool_name, tc.parameters)
        for tc in tool_calls
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

---

## 5. Monitoring and Observability

### 5.1 Structured Logging

**Log all key events:**

```python
import structlog

logger = structlog.get_logger()

# At orchestrator start
logger.info(
    "react_execution_started",
    user_input=context.user_input,
    max_iterations=self.max_iterations,
    model=self.provider.model,
)

# For each tool call
logger.info(
    "tool_call_attempted",
    tool_name=tool_call.tool_name,
    parameters=tool_call.parameters,
    iteration=iteration,
)

# For each tool result
logger.info(
    "tool_call_completed",
    tool_name=tool_call.tool_name,
    success=result.success,
    duration_ms=duration,
)

# At completion
logger.info(
    "react_execution_completed",
    iterations=iteration,
    tool_calls=tool_calls_count,
    success_rate=success_rate,
    duration_ms=total_duration,
)
```

### 5.2 Metrics Dashboard (Recommended)

**Export metrics to monitoring system:**

```python
# Export to Prometheus
from prometheus_client import Counter, Histogram, Gauge

tool_calls_total = Counter(
    'react_tool_calls_total',
    'Total tool calls attempted',
    ['tool_name', 'success']
)

iterations_histogram = Histogram(
    'react_iterations',
    'Number of iterations per execution'
)

success_rate_gauge = Gauge(
    'react_success_rate',
    'Current tool call success rate'
)

# Update metrics
tool_calls_total.labels(tool_name=name, success=str(success)).inc()
iterations_histogram.observe(iteration)
success_rate_gauge.set(success_rate)
```

### 5.3 Alerting Thresholds

**Set up alerts for degraded performance:**

```yaml
# Alert configuration
alerts:
  - name: "ReAct Success Rate Low"
    condition: "react_success_rate < 0.70"
    severity: "warning"
    message: "ReAct tool call success rate below 70%"

  - name: "ReAct Success Rate Critical"
    condition: "react_success_rate < 0.50"
    severity: "critical"
    message: "ReAct tool call success rate below 50% - check model/config"

  - name: "Max Iterations Reached Frequently"
    condition: "react_max_iterations_rate > 0.10"
    severity: "warning"
    message: "More than 10% of queries hitting max iterations"

  - name: "XML Parse Rate Low"
    condition: "react_xml_parse_rate < 0.40"
    severity: "warning"
    message: "XML parse rate below 40% - check prompt examples"
```

---

## 6. Testing Strategies

### 6.1 Unit Tests

**Test parser independently:**

```python
# tests/ai/test_react_orchestration.py

def test_parser_xml_valid():
    """Test XML parsing with valid input."""
    parser = ToolCallParser()
    response = """
<thought>Need to get stats</thought>
<action>get_invoice_stats</action>
<action_input>{"year": 2025}</action_input>
"""
    parsed = parser.parse(response)

    assert parsed.is_final is False
    assert parsed.tool_call.tool_name == "get_invoice_stats"
    assert parsed.tool_call.parameters == {"year": 2025}

def test_parser_fallback_to_legacy():
    """Test fallback when XML not present."""
    parser = ToolCallParser()
    response = """
Thought: Need to get stats
Action: get_invoice_stats
Action Input: {"year": 2025}
"""
    parsed = parser.parse(response)

    assert parsed.is_final is False
    assert parsed.tool_call.tool_name == "get_invoice_stats"
```

### 6.2 Integration Tests

**Test with mock provider and tools:**

```python
# tests/ai/test_react_orchestration_integration.py

@pytest.mark.asyncio
async def test_orchestrator_single_tool_call(
    mock_provider, mock_tool_registry
):
    """Test successful single tool call."""
    # Setup mock responses
    mock_provider._response_queue = [
        '<thought>Get stats</thought><action>get_invoice_stats</action><action_input>{}</action_input>',
        '<thought>Done</thought><final_answer>You have 42 invoices</final_answer>',
    ]

    # Execute
    orchestrator = ReActOrchestrator(mock_provider, mock_tool_registry)
    result = await orchestrator.execute(context)

    # Verify
    assert "42 invoices" in result
    assert orchestrator.metrics["tool_calls_succeeded"] == 1
```

### 6.3 E2E Tests

**Test with real Ollama:**

```python
# tests/ai/test_react_e2e_ollama.py

@pytest.mark.e2e
@pytest.mark.ollama
async def test_e2e_invoice_query(ollama_qwen3_provider):
    """E2E test with real Ollama."""
    # Requires: ollama serve && ollama pull qwen3:8b

    orchestrator = ReActOrchestrator(
        provider=ollama_qwen3_provider,
        tool_registry=tool_registry,
        max_iterations=5,
    )

    result = await orchestrator.execute(ChatContext(
        user_input="Quante fatture ho emesso quest'anno?",
        enable_tools=True,
    ))

    # Should contain real data from tools
    assert result is not None
    assert any(str(num) in result for num in [42, "42", "quarantadue"])

    # Check metrics
    metrics = orchestrator.get_metrics()
    assert metrics["tool_call_success_rate"] >= 0.8
```

### 6.4 Success Rate Testing

**Validate across diverse queries:**

```python
@pytest.mark.slow
async def test_success_rate_across_10_queries(ollama_provider):
    """Validate ≥80% success rate across diverse queries."""
    test_queries = [
        "Quante fatture ho emesso?",
        "Mostra le ultime fatture",
        "Chi è il cliente Acme?",
        # ... 7 more queries
    ]

    successes = 0
    for query in test_queries:
        result = await orchestrator.execute(ChatContext(
            user_input=query,
            enable_tools=True,
        ))

        # Check if result contains real data (not hallucinated)
        if any(real_data_indicator in result for real_data_indicator in [...]):
            successes += 1

    success_rate = successes / len(test_queries)
    assert success_rate >= 0.8, f"Success rate {success_rate:.2%} below 80%"
```

---

## 7. Common Pitfalls and Solutions

### 7.1 Low Success Rate

**Problem:** Tool call success rate below 70%

**Diagnosis:**
```python
metrics = orchestrator.get_metrics()
print(f"Success rate: {metrics['tool_call_success_rate']:.2%}")
print(f"XML parse rate: {metrics['parser_stats']['xml_parse_rate']:.2%}")
print(f"Avg iterations: {metrics['avg_iterations']:.2f}")
```

**Solutions:**
1. **Check temperature**: Must be 0.0
   ```python
   assert provider.temperature == 0.0
   ```

2. **Verify model**: Should be qwen3:8b
   ```python
   assert provider.model == "qwen3:8b"
   ```

3. **Improve prompt**: Add more few-shot examples
   ```python
   # Add 2-3 examples per tool in system prompt
   ```

4. **Check tool schemas**: Ensure clear descriptions
   ```python
   # Tool descriptions should be detailed and unambiguous
   ```

### 7.2 Infinite Loops

**Problem:** Orchestrator repeatedly calls same tool with same parameters

**Diagnosis:**
```python
# Log conversation history
for msg in conversation_messages:
    print(f"{msg.role}: {msg.content[:100]}...")
```

**Solutions:**
1. **Check tool output**: Ensure tool returns expected data
   ```python
   result = await tool_registry.execute_tool(tool_name, params)
   assert result.success
   assert result.data  # Not empty
   ```

2. **Format observations clearly**: Make results unambiguous
   ```python
   def _format_observation(self, data: Any) -> str:
       if isinstance(data, dict):
           return "\n".join(f"{k}: {v}" for k, v in data.items())
       return str(data)
   ```

3. **Add variation detection**: Detect repeated calls
   ```python
   last_calls = []
   if (tool_name, params) in last_calls[-3:]:
       observation = "Already tried this. Try a different approach."
   ```

### 7.3 Max Iterations Frequently Reached

**Problem:** >10% of queries hit max_iterations

**Diagnosis:**
```python
rate = metrics["max_iterations_reached"] / metrics["total_executions"]
print(f"Max iterations reached rate: {rate:.2%}")
```

**Solutions:**
1. **Increase max_iterations** for complex queries
   ```python
   orchestrator = ReActOrchestrator(max_iterations=10)  # Up from 5
   ```

2. **Break down complex queries**: Guide user to simpler questions
   ```python
   if complexity_score > threshold:
       return "This query is complex. Please break it into smaller questions."
   ```

3. **Optimize tool performance**: Reduce latency
   ```python
   # Cache frequently accessed data
   # Optimize database queries
   # Use indexes
   ```

### 7.4 Low XML Parse Rate

**Problem:** XML parse rate below 50% (falling back to legacy often)

**Solutions:**
1. **Add more XML examples** in system prompt
2. **Use qwen3:8b model** (better XML generation)
3. **Check model version**: Ensure using latest
   ```bash
   ollama pull qwen3:8b  # Re-pull to get latest version
   ```

---

## 8. Production Deployment

### 8.1 Pre-Deployment Checklist

- [ ] **Configuration validated**
  - [ ] Temperature = 0.0
  - [ ] Model = qwen3:8b (or approved alternative)
  - [ ] Max iterations appropriate (5-8)

- [ ] **Testing completed**
  - [ ] Unit tests passing (parser, orchestrator)
  - [ ] Integration tests passing (mock tools)
  - [ ] E2E tests passing (real Ollama, ≥80% success)
  - [ ] Success rate test passing (10 queries)

- [ ] **Observability configured**
  - [ ] Structured logging enabled
  - [ ] Metrics exported (Prometheus/Grafana)
  - [ ] Alerts configured (success rate, iterations)
  - [ ] Dashboards created

- [ ] **Documentation updated**
  - [ ] CLAUDE.md includes ReAct section
  - [ ] AI_ARCHITECTURE.md includes ReAct details
  - [ ] This best practices guide reviewed

### 8.2 Deployment Configuration

**Production .env:**
```bash
# AI Provider
OPENFATTURE_AI_PROVIDER=ollama
OPENFATTURE_AI_OLLAMA_MODEL=qwen3:8b
OPENFATTURE_AI_OLLAMA_BASE_URL=http://localhost:11434
OPENFATTURE_AI_TEMPERATURE=0.0

# ReAct Configuration
OPENFATTURE_AI_REACT_MAX_ITERATIONS=8
OPENFATTURE_AI_REACT_ENABLE_CACHING=true
OPENFATTURE_AI_REACT_LOG_LEVEL=INFO

# Monitoring
OPENFATTURE_AI_METRICS_ENABLED=true
OPENFATTURE_AI_METRICS_EXPORT=prometheus
```

### 8.3 Monitoring Plan

**Daily:**
- Check success rate dashboard (should be ≥80%)
- Review error logs for patterns
- Monitor latency percentiles (p50, p95, p99)

**Weekly:**
- Analyze failed queries (why did they fail?)
- Review max iterations reached cases
- Update prompt examples if needed

**Monthly:**
- Compare performance across models
- Evaluate new model releases
- Update benchmarks and thresholds

### 8.4 Rollback Plan

**If issues occur in production:**

1. **Immediate mitigation** - Switch to OpenAI/Anthropic
   ```bash
   export OPENFATTURE_AI_PROVIDER=openai
   export OPENFATTURE_AI_OPENAI_MODEL=gpt-4o
   ```

2. **Diagnose issue** - Check metrics and logs
   ```python
   metrics = orchestrator.get_metrics()
   logs = get_recent_logs(hours=1)
   ```

3. **Fix and retest** - Apply fix in dev/staging first

4. **Gradual rollout** - A/B test with 10% traffic

---

## 9. Future Improvements

### 9.1 Planned Enhancements

**Q4 2025:**
- [ ] Parallel tool execution for independent tools
- [ ] Adaptive max_iterations based on query complexity
- [ ] Automatic prompt optimization based on failures
- [ ] Multi-model ensemble (combine multiple LLMs)

**Q1 2026:**
- [ ] Fine-tuned qwen3 model for OpenFatture tools
- [ ] Self-healing prompts (auto-adjust based on metrics)
- [ ] Advanced caching with semantic similarity
- [ ] ReAct benchmarking suite

### 9.2 Research Areas

- **Better parsing**: Explore structured output formats (JSON mode)
- **Smarter iteration limits**: ML model to predict required iterations
- **Tool chaining**: Automatically chain related tools
- **Error recovery**: Self-correction when tool calls fail

---

## 10. Quick Reference

### Configuration Checklist

```bash
✅ Temperature = 0.0 (CRITICAL)
✅ Model = qwen3:8b
✅ Max iterations = 5-8
✅ XML format in prompts
✅ Few-shot examples (2-3 per tool)
✅ Metrics tracking enabled
✅ Structured logging enabled
```

### Key Metrics Targets

```python
tool_call_success_rate ≥ 0.80  # 80%
xml_parse_rate ≥ 0.60           # 60%
avg_iterations ≤ 3.0            # 3 iterations
max_iterations_reached ≤ 0.05   # 5%
```

### Testing Commands

```bash
# Unit tests
uv run pytest tests/ai/test_react_orchestration.py -v

# Integration tests
uv run pytest tests/ai/test_react_orchestration_integration.py -v

# E2E tests (requires Ollama)
uv run pytest tests/ai/test_react_e2e_ollama.py -v -m "ollama and e2e"

# Success rate validation
uv run pytest tests/ai/test_react_e2e_ollama.py::TestReActOllamaSuccessRate -v
```

### Troubleshooting Quick Guide

| Symptom | Check | Fix |
|---------|-------|-----|
| Low success rate | Temperature, model | Set temp=0.0, use qwen3:8b |
| Infinite loops | Tool outputs | Validate tool returns expected data |
| Max iterations | Query complexity | Increase max_iterations or split query |
| Low XML parse | Prompt examples | Add more XML examples in prompt |
| High latency | Tool performance | Cache data, optimize queries |

---

## References

- [AI Architecture Documentation](../AI_ARCHITECTURE.md#5-react-orchestration)
- [CLAUDE.md](../../CLAUDE.md#react-orchestration-new)
- [ReAct Paper (2022)](https://arxiv.org/abs/2210.03629)
- [Ollama Documentation](https://ollama.com/docs)
- [qwen3 Model Card](https://ollama.com/library/qwen3)

---

**Questions or Issues?**
- GitHub Issues: https://github.com/venerelabs/openfatture/issues
- Documentation: https://docs.openfatture.dev
- Community: https://discord.gg/openfatture
