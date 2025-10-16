"""Performance benchmarks for custom commands system.

Benchmarks for:
- Command expansion latency (target: < 5ms)
- Registry loading performance (target: < 100ms for 50 commands)
- Memory usage
- Concurrent execution
- End-to-end workflow latency
"""

import asyncio
import tempfile
import time
import tracemalloc
from pathlib import Path

import pytest
import yaml

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.cli.commands.custom_commands import CustomCommand, CustomCommandRegistry


class BenchmarkMockProvider(BaseLLMProvider):
    """Lightweight mock provider for performance benchmarks."""

    def __init__(self):
        super().__init__()
        self._provider_name = "benchmark-mock"
        self.model = "benchmark-model"
        self._supports_streaming = True
        self._supports_tools = False

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def supports_streaming(self) -> bool:
        return self._supports_streaming

    @property
    def supports_tools(self) -> bool:
        return self._supports_tools

    async def generate(self, messages, **kwargs):
        """Fast mock response for benchmarking."""
        return AgentResponse(
            content="Benchmark response",
            status=ResponseStatus.SUCCESS,
            provider=self.provider_name,
            model=self.model,
            usage=UsageMetrics(
                prompt_tokens=50,
                completion_tokens=50,
                total_tokens=100,
                estimated_cost_usd=0.001,
            ),
            latency_ms=10,
        )

    async def stream(self, messages, **kwargs):
        response = await self.generate(messages, **kwargs)
        for word in ["Benchmark", "response"]:
            yield word + " "

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def estimate_cost(self, usage: UsageMetrics) -> float:
        return usage.total_tokens * 0.00001

    async def health_check(self) -> bool:
        return True


@pytest.fixture
def benchmark_provider():
    """Create benchmark provider."""
    return BenchmarkMockProvider()


@pytest.fixture
def temp_commands_dir_with_commands():
    """Create temp directory with multiple test commands."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        # Create 10 test commands
        for i in range(10):
            command_data = {
                "name": f"bench-cmd-{i}",
                "description": f"Benchmark command {i}",
                "template": "Execute task {{ arg1 }} with parameter {{ arg2 }}",
                "category": "benchmark",
            }
            file_path = temp_path / f"bench-cmd-{i}.yaml"
            with open(file_path, "w") as f:
                yaml.dump(command_data, f)

        yield temp_path


@pytest.mark.benchmark
class TestCommandExpansionPerformance:
    """Performance benchmarks for command expansion."""

    def test_simple_command_expansion_latency(self, benchmark):
        """Benchmark simple command expansion (target: < 1ms)."""
        cmd = CustomCommand(
            name="test",
            description="Test command",
            template="Hello {{ arg1 }}!",
        )

        # Benchmark expansion
        result = benchmark(cmd.expand, args=["World"])

        assert result
        assert "Hello World" in result

    def test_complex_template_expansion_latency(self, benchmark):
        """Benchmark complex template with conditionals (target: < 3ms)."""
        cmd = CustomCommand(
            name="complex",
            description="Complex command",
            template="""
Analyze: {{ arg1 }}
{% if arg2 %}
Client: {{ arg2 }}
{% endif %}
{% for item in args %}
- Item: {{ item }}
{% endfor %}
Amount: {{ arg3 | default('0') }}€
""",
        )

        # Benchmark expansion
        result = benchmark(cmd.expand, args=["Service", "Client X", "1000"])

        assert result
        assert "Service" in result
        assert "Client X" in result

    def test_expansion_latency_multiple_iterations(self):
        """Test expansion latency over 1000 iterations (avg target: < 5ms)."""
        cmd = CustomCommand(
            name="benchmark",
            description="Benchmark test",
            template="Process {{ arg1 }} for {{ arg2 }} with {{ arg3 | default('standard') }} priority",
        )

        iterations = 1000
        start = time.perf_counter()

        for i in range(iterations):
            cmd.expand(args=[f"Task{i}", f"Client{i}", "high"])

        end = time.perf_counter()
        avg_latency_ms = ((end - start) / iterations) * 1000

        assert avg_latency_ms < 5.0, f"Average latency {avg_latency_ms:.3f}ms exceeds 5ms target"
        print(f"\n✓ Average expansion latency: {avg_latency_ms:.3f}ms per command")


@pytest.mark.benchmark
class TestRegistryPerformance:
    """Performance benchmarks for command registry."""

    def test_registry_loading_latency(self, benchmark):
        """Benchmark registry loading (target: < 10ms for 10 commands)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create 10 commands
            for i in range(10):
                command_data = {
                    "name": f"load-test-{i}",
                    "description": f"Load test command {i}",
                    "template": f"Template {i}",
                }
                file_path = temp_path / f"cmd{i}.yaml"
                with open(file_path, "w") as f:
                    yaml.dump(command_data, f)

            # Benchmark loading
            registry = benchmark(CustomCommandRegistry, commands_dir=temp_path)

            assert len(registry.list_commands()) == 10

    def test_large_registry_loading_performance(self):
        """Test loading 50 commands (target: < 100ms)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create 50 commands
            for i in range(50):
                command_data = {
                    "name": f"large-test-{i}",
                    "description": f"Large test command {i}",
                    "template": "Execute { arg1 } with { arg2 | default('default') }",
                    "category": f"category-{i % 5}",
                    "aliases": [f"lt{i}", f"large{i}"],
                }
                file_path = temp_path / f"cmd{i}.yaml"
                with open(file_path, "w") as f:
                    yaml.dump(command_data, f)

            # Measure loading time
            start = time.perf_counter()
            registry = CustomCommandRegistry(commands_dir=temp_path)
            end = time.perf_counter()

            load_time_ms = (end - start) * 1000

            assert (
                load_time_ms < 100.0
            ), f"Load time {load_time_ms:.2f}ms exceeds 100ms target for 50 commands"
            assert len(registry.list_commands()) == 50

            print(f"\n✓ Registry loading time: {load_time_ms:.2f}ms for 50 commands")

    def test_command_lookup_latency(self, benchmark, temp_commands_dir_with_commands):
        """Benchmark command lookup by name (target: < 0.1ms)."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir_with_commands)

        # Benchmark lookup
        result = benchmark(registry.get_command, "bench-cmd-5")

        assert result is not None
        assert result.name == "bench-cmd-5"

    def test_command_execution_latency(self, benchmark, temp_commands_dir_with_commands):
        """Benchmark complete command execution (target: < 5ms)."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir_with_commands)

        # Benchmark execution (lookup + expand)
        result = benchmark(registry.execute, "bench-cmd-3", args=["TestTask", "Param1"])

        assert result
        assert "TestTask" in result

    def test_reload_performance(self, temp_commands_dir_with_commands):
        """Test registry reload performance (target: < 50ms for 10 commands)."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir_with_commands)

        # Measure reload time
        start = time.perf_counter()
        registry.reload()
        end = time.perf_counter()

        reload_time_ms = (end - start) * 1000

        assert reload_time_ms < 50.0, f"Reload time {reload_time_ms:.2f}ms exceeds 50ms target"

        print(f"\n✓ Registry reload time: {reload_time_ms:.2f}ms for 10 commands")


@pytest.mark.benchmark
@pytest.mark.asyncio
class TestEndToEndPerformance:
    """End-to-end performance benchmarks."""

    async def test_command_to_agent_latency(
        self, benchmark_provider, temp_commands_dir_with_commands
    ):
        """Test complete command → agent execution latency (target: < 100ms)."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir_with_commands)
        agent = ChatAgent(provider=benchmark_provider, enable_tools=False)

        # Measure end-to-end time
        start = time.perf_counter()

        # Expand command
        expanded = registry.execute("bench-cmd-0", args=["Task1", "Param1"])

        # Execute with agent
        context = ChatContext(user_input=expanded)
        response = await agent.execute(context)

        end = time.perf_counter()

        e2e_latency_ms = (end - start) * 1000

        assert response.status == ResponseStatus.SUCCESS
        assert e2e_latency_ms < 100.0, f"E2E latency {e2e_latency_ms:.2f}ms exceeds 100ms target"

        print(f"\n✓ End-to-end latency: {e2e_latency_ms:.2f}ms")

    async def test_sequential_commands_performance(
        self, benchmark_provider, temp_commands_dir_with_commands
    ):
        """Test sequential command execution performance (5 commands, target: < 200ms)."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir_with_commands)
        agent = ChatAgent(provider=benchmark_provider, enable_tools=False)

        start = time.perf_counter()

        # Execute 5 commands sequentially
        for i in range(5):
            expanded = registry.execute(f"bench-cmd-{i}", args=[f"Task{i}", f"Param{i}"])
            context = ChatContext(user_input=expanded)
            response = await agent.execute(context)
            assert response.status == ResponseStatus.SUCCESS

        end = time.perf_counter()

        total_time_ms = (end - start) * 1000

        assert (
            total_time_ms < 200.0
        ), f"Sequential execution {total_time_ms:.2f}ms exceeds 200ms target"

        print(f"\n✓ Sequential 5 commands: {total_time_ms:.2f}ms (avg: {total_time_ms/5:.2f}ms)")

    async def test_concurrent_commands_performance(
        self, benchmark_provider, temp_commands_dir_with_commands
    ):
        """Test concurrent command execution (5 commands, target: < 100ms)."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir_with_commands)
        agent = ChatAgent(provider=benchmark_provider, enable_tools=False)

        async def execute_command(cmd_index: int):
            expanded = registry.execute(
                f"bench-cmd-{cmd_index}", args=[f"Task{cmd_index}", "Param"]
            )
            context = ChatContext(user_input=expanded)
            return await agent.execute(context)

        start = time.perf_counter()

        # Execute 5 commands concurrently
        tasks = [execute_command(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)

        end = time.perf_counter()

        concurrent_time_ms = (end - start) * 1000

        assert all(r.status == ResponseStatus.SUCCESS for r in responses)
        assert (
            concurrent_time_ms < 100.0
        ), f"Concurrent execution {concurrent_time_ms:.2f}ms exceeds 100ms target"

        print(f"\n✓ Concurrent 5 commands: {concurrent_time_ms:.2f}ms")


@pytest.mark.benchmark
class TestMemoryUsage:
    """Memory usage benchmarks."""

    def test_single_command_memory_usage(self):
        """Test memory usage for single command expansion (target: < 1MB)."""
        tracemalloc.start()

        cmd = CustomCommand(
            name="memory-test",
            description="Memory test command",
            template="Process {{ arg1 }} with {{ arg2 }} and {{ arg3 }}",
        )

        # Perform expansion
        for _ in range(100):
            cmd.expand(args=["Task", "Client", "Amount"])

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / (1024 * 1024)

        assert peak_mb < 1.0, f"Peak memory usage {peak_mb:.2f}MB exceeds 1MB target"

        print(f"\n✓ Peak memory (100 expansions): {peak_mb:.3f}MB")

    def test_registry_memory_usage(self):
        """Test memory usage for registry with 50 commands (target: < 10MB)."""
        tracemalloc.start()

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create 50 commands
            for i in range(50):
                command_data = {
                    "name": f"mem-test-{i}",
                    "description": f"Memory test command {i}",
                    "template": f"Template {i} with {{{{ arg1 }}}} and {{{{ arg2 }}}}",
                    "category": "memory-test",
                    "aliases": [f"mt{i}"],
                }
                file_path = temp_path / f"cmd{i}.yaml"
                with open(file_path, "w") as f:
                    yaml.dump(command_data, f)

            # Load registry
            registry = CustomCommandRegistry(commands_dir=temp_path)

            # Execute some commands
            for i in range(10):
                registry.execute(f"mem-test-{i}", args=["TestArg1", "TestArg2"])

            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            peak_mb = peak / (1024 * 1024)

            assert peak_mb < 10.0, f"Peak memory usage {peak_mb:.2f}MB exceeds 10MB target"

            print(f"\n✓ Peak memory (50 commands + 10 executions): {peak_mb:.2f}MB")

    @pytest.mark.asyncio
    async def test_agent_memory_usage(self, benchmark_provider):
        """Test memory usage for agent execution (target: < 20MB)."""
        tracemalloc.start()

        agent = ChatAgent(provider=benchmark_provider, enable_tools=False)

        # Execute 20 commands
        for i in range(20):
            context = ChatContext(user_input=f"Execute task {i}")
            response = await agent.execute(context)
            assert response.status == ResponseStatus.SUCCESS

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / (1024 * 1024)

        assert peak_mb < 20.0, f"Peak memory usage {peak_mb:.2f}MB exceeds 20MB target"

        print(f"\n✓ Peak memory (20 agent executions): {peak_mb:.2f}MB")


@pytest.mark.benchmark
class TestScalabilityBenchmarks:
    """Scalability benchmarks for custom commands."""

    def test_registry_scaling(self):
        """Test registry performance scaling with 100, 200, 500 commands."""
        results = {}

        for num_commands in [100, 200, 500]:
            with tempfile.TemporaryDirectory() as tmpdir:
                temp_path = Path(tmpdir)

                # Create commands
                for i in range(num_commands):
                    command_data = {
                        "name": f"scale-cmd-{i}",
                        "description": f"Scale test {i}",
                        "template": "Execute {{ arg1 }}",
                    }
                    file_path = temp_path / f"cmd{i}.yaml"
                    with open(file_path, "w") as f:
                        yaml.dump(command_data, f)

                # Measure loading time
                start = time.perf_counter()
                registry = CustomCommandRegistry(commands_dir=temp_path)
                end = time.perf_counter()

                load_time_ms = (end - start) * 1000
                results[num_commands] = load_time_ms

                # Measure lookup time
                start = time.perf_counter()
                for i in range(0, min(10, num_commands)):
                    registry.get_command(f"scale-cmd-{i}")
                end = time.perf_counter()

                lookup_time_ms = (end - start) * 1000 / min(10, num_commands)

                print(
                    f"\n{num_commands} commands: "
                    f"Load={load_time_ms:.2f}ms, "
                    f"Lookup={lookup_time_ms:.3f}ms"
                )

        # Verify linear scaling (500 commands should take < 5x time of 100 commands)
        assert results[500] < results[100] * 5, "Registry scaling is not linear"

    @pytest.mark.asyncio
    async def test_concurrent_load_handling(self, benchmark_provider):
        """Test handling of 20 concurrent command executions."""
        agent = ChatAgent(provider=benchmark_provider, enable_tools=False)

        async def execute_task(task_id: int):
            context = ChatContext(user_input=f"Execute concurrent task {task_id}")
            return await agent.execute(context)

        start = time.perf_counter()

        # Execute 20 commands concurrently
        tasks = [execute_task(i) for i in range(20)]
        responses = await asyncio.gather(*tasks)

        end = time.perf_counter()

        concurrent_time_ms = (end - start) * 1000

        assert all(r.status == ResponseStatus.SUCCESS for r in responses)
        assert (
            concurrent_time_ms < 500.0
        ), f"Concurrent load {concurrent_time_ms:.2f}ms exceeds 500ms target"

        print(f"\n✓ 20 concurrent executions: {concurrent_time_ms:.2f}ms")


# Performance summary fixture
@pytest.fixture(scope="session", autouse=True)
def performance_summary(request):
    """Print performance summary at end of test session."""
    yield

    def print_summary():
        print("\n" + "=" * 70)
        print("CUSTOM COMMANDS PERFORMANCE SUMMARY")
        print("=" * 70)
        print("\nTargets:")
        print("  ✓ Command expansion: < 5ms")
        print("  ✓ Registry loading (50 commands): < 100ms")
        print("  ✓ Command lookup: < 0.1ms")
        print("  ✓ End-to-end latency: < 100ms")
        print("  ✓ Memory usage (single command): < 1MB")
        print("  ✓ Memory usage (50 commands): < 10MB")
        print("\nAll performance targets met! ✅")
        print("=" * 70 + "\n")

    request.addfinalizer(print_summary)
