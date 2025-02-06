import pytest
import os
import tempfile
from pathlib import Path
from chad.core.config.provider import YAMLConfigProvider
from chad.core.errors import ConfigurationError, InvalidConfigError


def create_temp_yaml(content: str) -> str:
    """Helper to create a temporary YAML file."""
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"test_config_{os.getpid()}.yaml")

    with open(temp_path, 'w') as f:
        f.write(content)

    return temp_path


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Cleanup temporary files after each test."""
    yield
    temp_dir = tempfile.gettempdir()
    for file in os.listdir(temp_dir):
        if file.startswith("test_config_") and file.endswith(".yaml"):
            try:
                os.unlink(os.path.join(temp_dir, file))
            except:
                pass


@pytest.fixture
def config_file():
    """Create a temporary config file."""
    content = """
    app:
      name: CHAD
      version: 1.0.0
    database:
      host: localhost
      port: 5432
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
    yield f.name
    os.unlink(f.name)


@pytest.fixture
def secrets_file():
    """Create a temporary secrets file."""
    content = """
    database:
      password: secret123
    api:
      key: abc123
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
    yield f.name
    os.unlink(f.name)


@pytest.mark.asyncio
async def test_basic_config_loading(config_file):
    """Test basic configuration loading."""
    provider = YAMLConfigProvider(config_file)
    await provider.initialize({})

    assert await provider.get("app.name") == "CHAD"
    assert await provider.get("database.port") == 5432


@pytest.mark.asyncio
async def test_secrets_loading(config_file, secrets_file):
    """Test secrets loading and merging."""
    provider = YAMLConfigProvider(config_file, secrets_path=secrets_file)
    await provider.initialize({})

    assert await provider.get("database.password") == "secret123"
    assert await provider.get("api.key") == "abc123"
    # Original config preserved
    assert await provider.get("app.name") == "CHAD"


@pytest.mark.asyncio
async def test_environment_override():
    """Test environment variable overrides."""
    config_path = create_temp_yaml("app:\n  name: CHAD\n")

    try:
        os.environ["CHAD_APP__NAME"] = "CHAD_ENV"
        os.environ["CHAD_NEW__VALUE"] = "42"  # This should be converted to int
        os.environ["CHAD_NEW__STRING"] = "text"  # This should stay string

        provider = YAMLConfigProvider(config_path)
        await provider.initialize({})

        assert await provider.get("app.name") == "CHAD_ENV"
        assert await provider.get("new.value") == 42  # Check for int
        assert await provider.get("new.string") == "text"  # Check for string
    finally:
        try:
            os.unlink(config_path)
        except:
            pass


@pytest.mark.asyncio
async def test_config_namespace(config_file):
    """Test getting configuration namespace."""
    provider = YAMLConfigProvider(config_file)
    await provider.initialize({})

    database_config = await provider.get_namespace("database")
    assert "database.host" in database_config
    assert "database.port" in database_config


@pytest.mark.asyncio
async def test_config_modification():
    """Test configuration modification."""
    config_path = create_temp_yaml("app:\n  name: CHAD\n")

    try:
        provider = YAMLConfigProvider(config_path)
        await provider.initialize({})

        await provider.set("app.version", "2.0.0")
        assert await provider.get("app.version") == "2.0.0"

        await provider.set("new.key", "value")
        assert await provider.get("new.key") == "value"
    finally:
        try:
            os.unlink(config_path)
        except:
            pass


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling."""
    # Non-existent file
    provider = YAMLConfigProvider("nonexistent.yaml")
    with pytest.raises(ConfigurationError):
        await provider.initialize({})

    # Invalid YAML
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
        f.write("invalid: yaml: :")
        f.flush()

        provider = YAMLConfigProvider(f.name)
        with pytest.raises(ConfigurationError):
            await provider.initialize({})


@pytest.mark.asyncio
async def test_type_conversion():
    """Test environment variable type conversion."""
    config_path = create_temp_yaml("app:\n  value: 1\n")

    try:
        os.environ["CHAD_APP__INT"] = "42"
        os.environ["CHAD_APP__FLOAT"] = "42.5"
        os.environ["CHAD_APP__BOOL"] = "true"
        os.environ["CHAD_APP__LIST"] = "[1, 2, 3]"

        provider = YAMLConfigProvider(config_path)
        await provider.initialize({})

        assert isinstance(await provider.get("app.int"), int)
        assert isinstance(await provider.get("app.float"), float)
        assert isinstance(await provider.get("app.bool"), bool)
        assert isinstance(await provider.get("app.list"), list)
    finally:
        try:
            os.unlink(config_path)
        except:
            pass
