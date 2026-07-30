import pytest

from app.providers.base import ModelProvider


def test_model_provider_is_abstract():
    """ModelProvider cannot be instantiated directly"""
    with pytest.raises(TypeError):
        ModelProvider()


def test_model_provider_requires_list_models():
    """Subclass must implement list_models"""
    class IncompleteProvider(ModelProvider):
        async def generate(self, model: str, prompt: str, context: str) -> str:
            return ""

        def is_available(self) -> bool:
            return True

    with pytest.raises(TypeError):
        IncompleteProvider()


def test_model_provider_requires_generate():
    """Subclass must implement generate"""
    class IncompleteProvider(ModelProvider):
        async def list_models(self):
            return []

        def is_available(self) -> bool:
            return True

    with pytest.raises(TypeError):
        IncompleteProvider()


def test_model_provider_requires_is_available():
    """Subclass must implement is_available"""
    class IncompleteProvider(ModelProvider):
        async def list_models(self):
            return []

        async def generate(self, model: str, prompt: str, context: str) -> str:
            return ""

    with pytest.raises(TypeError):
        IncompleteProvider()


def test_complete_provider_can_be_instantiated():
    """Subclass with all methods implemented can be instantiated"""
    class CompleteProvider(ModelProvider):
        async def list_models(self):
            return []

        async def generate(self, model: str, prompt: str, context: str) -> str:
            return "test"

        def is_available(self) -> bool:
            return True

    # Should not raise
    provider = CompleteProvider()
    assert isinstance(provider, ModelProvider)
