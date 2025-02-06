from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Set, List
from dataclasses import dataclass
from enum import Enum, auto, IntFlag
from datetime import datetime


class ProcessingStatus(IntFlag):
    """Core processing states that every processor must support"""
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()

    def __str__(self) -> str:
        return self.name.lower()

    def __repr__(self) -> str:
        return f"ProcessingStatus.{self.name}"

    @classmethod
    def get_terminal_states(cls) -> Set['ProcessingStatus']:
        """Returns states that represent end of processing"""
        return {cls.COMPLETED, cls.FAILED}

    @classmethod
    def get_active_states(cls) -> Set['ProcessingStatus']:
        """Returns states that represent active processing"""
        return {cls.PENDING, cls.PROCESSING}


@dataclass
class ProcessingContext:
    """Context object for passing state between processing stages"""
    status: ProcessingStatus
    metadata: Dict[str, Any]
    error: Optional[Exception] = None


class ContentProcessor(ABC):
    """Base interface for all content processing components

    A content processor is responsible for transforming content from one form to another.
    It maintains a clear contract for processing, validation, and state management.
    """

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the processor with configuration"""
        pass

    @abstractmethod
    async def process(self, content: Any, context: ProcessingContext) -> ProcessingContext:
        """Process the given content and update the context

        Args:
            content: The content to process
            context: The current processing context

        Returns:
            Updated ProcessingContext

        Raises:
            ProcessingError: If processing fails
            ValidationError: If content is invalid
        """
        pass

    @abstractmethod
    async def validate(self, content: Any) -> bool:
        """Validate if the content can be processed

        Args:
            content: The content to validate

        Returns:
            True if content is valid for this processor

        Raises:
            ValidationError: If validation fails with specific reason
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup any resources used by the processor"""
        pass


class Plugin(ABC):
    """Base interface for all plugins

    A plugin extends the system's functionality through a well-defined interface.
    It must manage its own lifecycle, provide clear metadata, and declare its capabilities.
    """

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with given configuration

        Args:
            config: Plugin configuration parameters

        Raises:
            PluginInitError: If initialization fails
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup and shutdown the plugin

        Raises:
            PluginShutdownError: If shutdown fails
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the plugin name"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Get the plugin version"""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> Set[str]:
        """Get plugin capabilities

        Returns:
            Set of capability identifiers this plugin provides
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if plugin is healthy and operational

        Returns:
            True if plugin is healthy
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Get plugin metadata

        Returns:
            Dictionary containing plugin metadata like:
            - description
            - author
            - dependencies
            - requirements
            - etc.
        """
        pass


class ConfigurationProvider(ABC):
    """Base interface for configuration management

    Responsible for managing all system configurations, including:
    - Environment settings
    - Secrets
    - System-wide settings
    - Feature flags
    - Plugin configurations
    - Template settings
    """

    @abstractmethod
    async def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value

        Args:
            key: Configuration key (supports dot notation for nested configs)
            default: Default value if key doesn't exist

        Returns:
            Configuration value

        Raises:
            ConfigurationError: If key format is invalid
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        """Set configuration value

        Args:
            key: Configuration key (supports dot notation for nested configs)
            value: Value to set

        Raises:
            ConfigurationError: If key format is invalid or value type is unsupported
        """
        pass

    @abstractmethod
    async def has(self, key: str) -> bool:
        """Check if configuration exists

        Args:
            key: Configuration key to check

        Returns:
            True if configuration exists
        """
        pass

    @abstractmethod
    async def load(self, config_source: str) -> None:
        """Load configuration from source

        Args:
            config_source: Source identifier (file path, env, etc)

        Raises:
            ConfigurationLoadError: If loading fails
        """
        pass

    @abstractmethod
    async def get_namespace(self, namespace: str) -> Dict[str, Any]:
        """Get all configurations under a namespace

        Args:
            namespace: Configuration namespace

        Returns:
            Dictionary of all configurations in namespace
        """
        pass


class MediaGenerator(ABC):
    """Base interface for media generation components

    Responsible for transforming processed content into final media outputs
    like videos, images, etc.
    """

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the generator with configuration"""
        pass

    @abstractmethod
    async def generate(self, content: Any, template: Any) -> Any:
        """Generate media output from content using template

        Args:
            content: Processed content to generate media from
            template: Template defining the media format/style

        Returns:
            Generated media output

        Raises:
            MediaGenerationError: If generation fails
            TemplateError: If template is invalid
        """
        pass

    @abstractmethod
    async def validate_output(self, output: Any) -> bool:
        """Validate generated media output

        Args:
            output: Generated media to validate

        Returns:
            True if output meets quality standards
        """
        pass


class TemplateManager(ABC):
    """Base interface for template management

    Handles loading, validation, and versioning of templates used
    throughout the system.
    """

    @abstractmethod
    async def load_template(self, template_id: str) -> Any:
        """Load template by ID

        Args:
            template_id: Unique template identifier

        Returns:
            Loaded template

        Raises:
            TemplateNotFoundError: If template doesn't exist
            TemplateLoadError: If loading fails
        """
        pass

    @abstractmethod
    async def validate_template(self, template: Any) -> bool:
        """Validate template structure and content

        Args:
            template: Template to validate

        Returns:
            True if template is valid

        Raises:
            TemplateValidationError: If validation fails with reason
        """
        pass

    @abstractmethod
    async def get_template_metadata(self, template_id: str) -> Dict[str, Any]:
        """Get template metadata

        Args:
            template_id: Template identifier

        Returns:
            Template metadata including version, dependencies, etc.
        """
        pass


class QualityValidator(ABC):
    """Base interface for quality validation

    Ensures content and media outputs meet quality standards
    through various validation rules.
    """

    @abstractmethod
    async def validate(self, content: Any, rule_set: str) -> bool:
        """Validate content against quality rules

        Args:
            content: Content to validate
            rule_set: Identifier for rule set to apply

        Returns:
            True if content meets quality standards

        Raises:
            ValidationError: If validation fails with details
        """
        pass

    @abstractmethod
    async def get_validation_report(self) -> Dict[str, Any]:
        """Get detailed validation results

        Returns:
            Dictionary containing validation metrics and issues
        """
        pass

    @abstractmethod
    async def register_rules(self, rule_set: str, rules: Dict[str, Any]) -> None:
        """Register new validation rules

        Args:
            rule_set: Identifier for rule set
            rules: Dictionary of rules to register
        """
        pass


class ContentSource(ABC):
    """Base interface for content source implementations

    Responsible for discovering and fetching content from various sources
    like files, APIs, databases, etc.
    """

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the content source"""
        pass

    @abstractmethod
    async def discover(self, criteria: Dict[str, Any]) -> List[Any]:
        """Discover available content matching criteria

        Args:
            criteria: Search/filter criteria for content discovery

        Returns:
            List of discovered content identifiers/metadata

        Raises:
            DiscoveryError: If discovery process fails
        """
        pass

    @abstractmethod
    async def fetch(self, content_id: str) -> Any:
        """Fetch specific content by ID

        Args:
            content_id: Unique content identifier

        Returns:
            The requested content

        Raises:
            ContentNotFoundError: If content doesn't exist
            FetchError: If retrieval fails
        """
        pass

    @abstractmethod
    async def validate(self, content: Any) -> bool:
        """Validate if content meets source requirements

        Args:
            content: Content to validate

        Returns:
            True if content is valid
        """
        pass


class PipelineOrchestrator(ABC):
    """Base interface for pipeline orchestration

    Manages the execution flow of content through various processing stages,
    coordinates resources, and tracks progress.
    """

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the orchestrator"""
        pass

    @abstractmethod
    async def execute_pipeline(self, content: Any, pipeline_id: str) -> Any:
        """Execute a processing pipeline on content

        Args:
            content: Content to process
            pipeline_id: Identifier for pipeline configuration

        Returns:
            Processing result

        Raises:
            PipelineNotFoundError: If pipeline doesn't exist
            PipelineExecutionError: If execution fails
        """
        pass

    @abstractmethod
    async def get_pipeline_status(self, execution_id: str) -> Dict[str, Any]:
        """Get status of pipeline execution

        Args:
            execution_id: Unique execution identifier

        Returns:
            Dictionary containing execution status and progress
        """
        pass

    @abstractmethod
    async def cancel_pipeline(self, execution_id: str) -> None:
        """Cancel a running pipeline

        Args:
            execution_id: Execution to cancel

        Raises:
            PipelineNotFoundError: If execution doesn't exist
        """
        pass


class LogLevel(Enum):
    """Standard log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Logger(ABC):
    """Base interface for logging system

    Provides structured logging with context tracking and 
    consistent formatting across the system.
    """

    @abstractmethod
    async def log(self, level: LogLevel, message: str, **context) -> None:
        """Log a message with given level and context

        Args:
            level: Severity level of the log
            message: Log message
            **context: Additional context data

        Raises:
            LoggingError: If logging fails
        """
        pass

    @abstractmethod
    async def start_operation(self, operation_name: str, **context) -> str:
        """Start tracking an operation

        Args:
            operation_name: Name of operation to track
            **context: Operation context data

        Returns:
            Operation tracking ID
        """
        pass

    @abstractmethod
    async def end_operation(self, operation_id: str, status: str) -> None:
        """End tracking an operation

        Args:
            operation_id: Operation tracking ID
            status: Final operation status
        """
        pass


class DataStore(ABC):
    """Base interface for data persistence

    Provides consistent data storage and retrieval across the system
    with support for different storage backends.
    """

    @abstractmethod
    async def store(self, key: str, data: Any, **options) -> None:
        """Store data with given key

        Args:
            key: Unique identifier for the data
            data: Data to store
            **options: Storage options (ttl, encoding, etc)

        Raises:
            StorageError: If storage fails
        """
        pass

    @abstractmethod
    async def retrieve(self, key: str) -> Any:
        """Retrieve data by key

        Args:
            key: Data identifier

        Returns:
            Stored data

        Raises:
            DataNotFoundError: If key doesn't exist
            RetrievalError: If retrieval fails
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete data by key

        Args:
            key: Data identifier to delete

        Raises:
            DataNotFoundError: If key doesn't exist
        """
        pass

    @abstractmethod
    async def list_keys(self, pattern: str = "*") -> List[str]:
        """List keys matching pattern

        Args:
            pattern: Key match pattern

        Returns:
            List of matching keys
        """
        pass
