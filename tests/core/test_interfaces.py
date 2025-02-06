import pytest
from chad.core.interfaces import (
    ProcessingStatus,
    ProcessingContext,
    ContentProcessor,
    Plugin,
    ConfigurationProvider,
    MediaGenerator,
    TemplateManager,
    QualityValidator,
    ContentSource,
    PipelineOrchestrator,
    Logger,
    LogLevel,
    DataStore
)
from typing import Any
from datetime import datetime

# Test ProcessingContext


def test_processing_context_creation():
    context = ProcessingContext(
        status=ProcessingStatus.PENDING,
        metadata={"test": "value"}
    )
    assert context.status == ProcessingStatus.PENDING
    assert context.metadata["test"] == "value"
    assert context.error is None

# Create mock implementations for testing


class MockContentProcessor(ContentProcessor):
    async def initialize(self, config):
        self.initialized = True
        self.config = config

    async def process(self, content, context):
        if not hasattr(self, 'initialized'):
            raise RuntimeError("Processor not initialized")
        context.status = ProcessingStatus.COMPLETED
        return context

    async def validate(self, content):
        return True

    async def cleanup(self):
        self.initialized = False


class MockPlugin(Plugin):
    async def initialize(self, config):
        self.initialized = True
        self.config = config

    async def shutdown(self):
        self.initialized = False

    @property
    def name(self):
        return "mock_plugin"

    @property
    def version(self):
        return "1.0.0"

    @property
    def capabilities(self):
        return {"process_text", "generate_video"}

    async def health_check(self):
        return hasattr(self, 'initialized') and self.initialized

    def get_metadata(self):
        return {
            "description": "A mock plugin for testing",
            "author": "CHAD Team",
            "dependencies": [],
            "requirements": ["python>=3.9"]
        }


class MockConfigProvider(ConfigurationProvider):
    def __init__(self):
        self.config = {}

    async def get(self, key: str, default: Any = None):
        return self.config.get(key, default)

    async def set(self, key: str, value: Any):
        self.config[key] = value

    async def has(self, key: str):
        return key in self.config

    async def load(self, config_source: str):
        if config_source == "test":
            self.config.update({
                "app.name": "CHAD",
                "app.version": "1.0.0"
            })

    async def get_namespace(self, namespace: str):
        return {
            k: v for k, v in self.config.items()
            if k.startswith(namespace)
        }


class MockMediaGenerator(MediaGenerator):
    async def initialize(self, config):
        self.config = config

    async def generate(self, content, template):
        return {"type": "video", "content": content, "template": template}

    async def validate_output(self, output):
        return isinstance(output, dict) and "type" in output


class MockTemplateManager(TemplateManager):
    def __init__(self):
        self.templates = {
            "basic": {"type": "video", "version": "1.0.0"},
            "advanced": {"type": "video", "version": "2.0.0"}
        }

    async def load_template(self, template_id):
        if template_id in self.templates:
            return self.templates[template_id]
        raise Exception("Template not found")

    async def validate_template(self, template):
        return isinstance(template, dict) and "type" in template

    async def get_template_metadata(self, template_id):
        if template_id in self.templates:
            return {"version": self.templates[template_id]["version"]}
        raise Exception("Template not found")


class MockQualityValidator(QualityValidator):
    def __init__(self):
        self.rules = {}
        self.last_validation = None

    async def validate(self, content, rule_set):
        self.last_validation = {"content": content, "rule_set": rule_set}
        return True

    async def get_validation_report(self):
        return self.last_validation or {}

    async def register_rules(self, rule_set, rules):
        self.rules[rule_set] = rules


class MockContentSource(ContentSource):
    def __init__(self):
        self.content = {
            "test1": "Test Content 1",
            "test2": "Test Content 2"
        }

    async def initialize(self, config):
        self.initialized = True

    async def discover(self, criteria):
        return [
            {"id": k, "preview": v[:10]}
            for k, v in self.content.items()
            if criteria.get("text", "") in v
        ]

    async def fetch(self, content_id):
        if content_id in self.content:
            return self.content[content_id]
        raise Exception("Content not found")

    async def validate(self, content):
        return isinstance(content, str)


class MockPipelineOrchestrator(PipelineOrchestrator):
    def __init__(self):
        self.pipelines = {}
        self.executions = {}

    async def initialize(self, config):
        self.initialized = True

    async def execute_pipeline(self, content, pipeline_id):
        execution_id = f"exec_{len(self.executions)}"
        self.executions[execution_id] = {
            "status": "running",
            "pipeline_id": pipeline_id,
            "content": content
        }
        return execution_id

    async def get_pipeline_status(self, execution_id):
        if execution_id in self.executions:
            return self.executions[execution_id]
        raise Exception("Execution not found")

    async def cancel_pipeline(self, execution_id):
        if execution_id in self.executions:
            self.executions[execution_id]["status"] = "cancelled"
        else:
            raise Exception("Execution not found")


class MockLogger(Logger):
    def __init__(self):
        self.logs = []
        self.operations = {}

    async def log(self, level: LogLevel, message: str, **context):
        self.logs.append({
            "level": level,
            "message": message,
            "context": context,
            "timestamp": datetime.now()
        })

    async def start_operation(self, operation_name: str, **context):
        operation_id = f"op_{len(self.operations)}"
        self.operations[operation_id] = {
            "name": operation_name,
            "context": context,
            "start_time": datetime.now(),
            "status": "started"
        }
        return operation_id

    async def end_operation(self, operation_id: str, status: str):
        if operation_id in self.operations:
            self.operations[operation_id]["status"] = status
            self.operations[operation_id]["end_time"] = datetime.now()


class MockDataStore(DataStore):
    def __init__(self):
        self.data = {}

    async def store(self, key: str, data: Any, **options):
        self.data[key] = {"data": data, "options": options}

    async def retrieve(self, key: str):
        if key in self.data:
            return self.data[key]["data"]
        raise Exception("Data not found")

    async def delete(self, key: str):
        if key in self.data:
            del self.data[key]
        else:
            raise Exception("Data not found")

    async def list_keys(self, pattern: str = "*"):
        return list(self.data.keys())


# Test ContentProcessor


@pytest.mark.asyncio
async def test_content_processor():
    processor = MockContentProcessor()
    context = ProcessingContext(
        status=ProcessingStatus.PENDING,
        metadata={}
    )

    # Test initialization
    await processor.initialize({"test": "config"})
    assert processor.initialized
    assert processor.config["test"] == "config"

    # Test process
    result = await processor.process("test content", context)
    assert result.status == ProcessingStatus.COMPLETED

    # Test validate
    is_valid = await processor.validate("test content")
    assert is_valid == True

    # Test cleanup
    await processor.cleanup()
    assert not processor.initialized

# Test Plugin


@pytest.mark.asyncio
async def test_plugin():
    plugin = MockPlugin()

    # Test initialization
    await plugin.initialize({"test": "config"})
    assert plugin.initialized
    assert plugin.config["test"] == "config"

    # Test properties
    assert plugin.name == "mock_plugin"
    assert plugin.version == "1.0.0"
    assert "process_text" in plugin.capabilities
    assert "generate_video" in plugin.capabilities

    # Test health check
    assert await plugin.health_check() == True

    # Test metadata
    metadata = plugin.get_metadata()
    assert metadata["author"] == "CHAD Team"
    assert metadata["description"] == "A mock plugin for testing"

    # Test shutdown
    await plugin.shutdown()
    assert not plugin.initialized
    assert await plugin.health_check() == False


@pytest.mark.asyncio
async def test_config_provider():
    provider = MockConfigProvider()

    # Test set/get
    await provider.set("test.key", "value")
    assert await provider.get("test.key") == "value"
    assert await provider.get("missing.key", "default") == "default"

    # Test has
    assert await provider.has("test.key") == True
    assert await provider.has("missing.key") == False

    # Test load
    await provider.load("test")
    assert await provider.get("app.name") == "CHAD"

    # Test namespace
    namespace_config = await provider.get_namespace("app")
    assert namespace_config["app.name"] == "CHAD"
    assert namespace_config["app.version"] == "1.0.0"


@pytest.mark.asyncio
async def test_media_generator():
    generator = MockMediaGenerator()

    # Test initialization
    await generator.initialize({"quality": "high"})
    assert generator.config["quality"] == "high"

    # Test generation
    output = await generator.generate("test content", "basic template")
    assert output["type"] == "video"
    assert output["content"] == "test content"

    # Test validation
    assert await generator.validate_output(output) == True


@pytest.mark.asyncio
async def test_template_manager():
    manager = MockTemplateManager()

    # Test template loading
    template = await manager.load_template("basic")
    assert template["type"] == "video"
    assert template["version"] == "1.0.0"

    # Test validation
    assert await manager.validate_template(template) == True

    # Test metadata
    metadata = await manager.get_template_metadata("basic")
    assert metadata["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_quality_validator():
    validator = MockQualityValidator()

    # Test rule registration
    rules = {"min_length": 10, "max_length": 100}
    await validator.register_rules("content_rules", rules)
    assert validator.rules["content_rules"] == rules

    # Test validation
    assert await validator.validate("test content", "content_rules") == True

    # Test report
    report = await validator.get_validation_report()
    assert report["content"] == "test content"
    assert report["rule_set"] == "content_rules"


@pytest.mark.asyncio
async def test_content_source():
    source = MockContentSource()

    # Test initialization
    await source.initialize({})
    assert source.initialized

    # Test discovery
    results = await source.discover({"text": "Test"})
    assert len(results) == 2
    assert results[0]["id"] == "test1"

    # Test fetch
    content = await source.fetch("test1")
    assert content == "Test Content 1"

    # Test validation
    assert await source.validate("Test content") == True
    assert await source.validate(123) == False


@pytest.mark.asyncio
async def test_pipeline_orchestrator():
    orchestrator = MockPipelineOrchestrator()

    # Test initialization
    await orchestrator.initialize({})
    assert orchestrator.initialized

    # Test execution
    execution_id = await orchestrator.execute_pipeline("test content", "basic_pipeline")
    assert execution_id.startswith("exec_")

    # Test status
    status = await orchestrator.get_pipeline_status(execution_id)
    assert status["status"] == "running"
    assert status["content"] == "test content"

    # Test cancellation
    await orchestrator.cancel_pipeline(execution_id)
    status = await orchestrator.get_pipeline_status(execution_id)
    assert status["status"] == "cancelled"


@pytest.mark.asyncio
async def test_logger():
    logger = MockLogger()

    # Test basic logging
    await logger.log(LogLevel.INFO, "Test message", user="test")
    assert len(logger.logs) == 1
    assert logger.logs[0]["level"] == LogLevel.INFO
    assert logger.logs[0]["message"] == "Test message"

    # Test operation tracking
    op_id = await logger.start_operation("test_op", user="test")
    assert op_id in logger.operations
    assert logger.operations[op_id]["status"] == "started"

    await logger.end_operation(op_id, "completed")
    assert logger.operations[op_id]["status"] == "completed"


@pytest.mark.asyncio
async def test_data_store():
    store = MockDataStore()

    # Test store/retrieve
    await store.store("test_key", {"value": "test"}, ttl=3600)
    data = await store.retrieve("test_key")
    assert data["value"] == "test"

    # Test list keys
    keys = await store.list_keys()
    assert "test_key" in keys

    # Test delete
    await store.delete("test_key")
    keys = await store.list_keys()
    assert len(keys) == 0
