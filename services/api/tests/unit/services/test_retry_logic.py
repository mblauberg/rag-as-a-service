"""Tests for retry logic in HTTP services."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from tenacity import RetryError

from app.core.exceptions import ServiceUnavailableError, EmbeddingServiceError, GenerationServiceError, ValidationError
from app.infrastructure.services.embedding_service import HTTPEmbeddingService
from app.services.generator_client import GeneratorClient


class TestEmbeddingServiceRetry:
    """Test retry behavior for HTTPEmbeddingService."""

    @pytest.mark.asyncio
    async def test_embedding_service_retries_on_connection_error(self) -> None:
        """Test that embedding service retries on connection errors."""
        service = HTTPEmbeddingService("http://localhost:8001")

        with patch("httpx.AsyncClient") as mock_client_class:
            # Create a mock client that raises ConnectError
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_client_class.return_value = mock_client

            # Should raise RetryError after 3 retries
            with pytest.raises(RetryError):
                await service.generate_embeddings(["test text"])

            # Verify it tried 3 times (with retries)
            assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_embedding_service_retries_on_timeout(self) -> None:
        """Test that embedding service retries on timeout."""
        service = HTTPEmbeddingService("http://localhost:8001")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.side_effect = httpx.TimeoutException("Request timed out")
            mock_client_class.return_value = mock_client

            with pytest.raises(RetryError):
                await service.generate_embeddings(["test text"])

            assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_embedding_service_retries_on_503(self) -> None:
        """Test that embedding service retries on 503 status code."""
        service = HTTPEmbeddingService("http://localhost:8001")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            # Create a proper mock for HTTPStatusError
            mock_request = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 503

            def raise_503(*args, **kwargs):
                raise httpx.HTTPStatusError("Service unavailable", request=mock_request, response=mock_response)

            mock_client.post.return_value.raise_for_status = raise_503
            mock_client_class.return_value = mock_client

            with pytest.raises(RetryError):
                await service.generate_embeddings(["test text"])

            assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_embedding_service_succeeds_after_retry(self) -> None:
        """Test that embedding service succeeds after initial failures."""
        service = HTTPEmbeddingService("http://localhost:8001")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            # Fail twice, then succeed
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}
            mock_response_success.raise_for_status.return_value = None

            call_count = 0
            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise httpx.ConnectError("Connection refused")
                return mock_response_success

            mock_client.post.side_effect = side_effect
            mock_client_class.return_value = mock_client

            result = await service.generate_embeddings(["test text"])

            assert result == [[0.1, 0.2, 0.3]]
            assert mock_client.post.call_count == 3  # Failed 2 times, succeeded on 3rd

    @pytest.mark.asyncio
    async def test_embedding_service_does_not_retry_on_validation_error(self) -> None:
        """Test that embedding service does not retry on validation errors."""
        service = HTTPEmbeddingService("http://localhost:8001")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            # Return invalid response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}  # Missing 'embeddings' key
            mock_response.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            # ValidationError should not trigger retry
            # Since it's not ServiceUnavailableError, no retry happens
            with pytest.raises(ValidationError):
                await service.generate_embeddings(["test text"])

            # Should only try once (no retry for validation errors)
            assert mock_client.post.call_count == 1


class TestGeneratorClientRetry:
    """Test retry behavior for GeneratorClient."""

    @pytest.mark.asyncio
    async def test_generator_retries_on_connection_error(self) -> None:
        """Test that generator client retries on connection errors."""
        client = GeneratorClient("http://localhost:8002")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_http_client = AsyncMock()
            mock_http_client.__aenter__.return_value = mock_http_client
            mock_http_client.__aexit__.return_value = None
            mock_http_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_client_class.return_value = mock_http_client

            with pytest.raises(RetryError):
                await client.generate_summary("test query", [{"text": "test", "document_id": "123", "chunk_index": 0}], "gpt-4o-mini")

            assert mock_http_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_generator_retries_on_timeout(self) -> None:
        """Test that generator client retries on timeout."""
        client = GeneratorClient("http://localhost:8002")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_http_client = AsyncMock()
            mock_http_client.__aenter__.return_value = mock_http_client
            mock_http_client.__aexit__.return_value = None
            mock_http_client.post.side_effect = httpx.TimeoutException("Request timed out")
            mock_client_class.return_value = mock_http_client

            with pytest.raises(RetryError):
                await client.generate_summary("test query", [{"text": "test", "document_id": "123", "chunk_index": 0}], "gpt-4o-mini")

            assert mock_http_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_generator_retries_on_503(self) -> None:
        """Test that generator client retries on 503 status code."""
        client = GeneratorClient("http://localhost:8002")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_http_client = AsyncMock()
            mock_http_client.__aenter__.return_value = mock_http_client
            mock_http_client.__aexit__.return_value = None

            mock_response = MagicMock()
            mock_response.status_code = 503
            mock_http_client.post.return_value = mock_response
            mock_client_class.return_value = mock_http_client

            with pytest.raises(RetryError):
                await client.generate_summary("test query", [{"text": "test", "document_id": "123", "chunk_index": 0}], "gpt-4o-mini")

            assert mock_http_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_generator_succeeds_after_retry(self) -> None:
        """Test that generator client succeeds after initial failures."""
        client = GeneratorClient("http://localhost:8002")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_http_client = AsyncMock()
            mock_http_client.__aenter__.return_value = mock_http_client
            mock_http_client.__aexit__.return_value = None

            # Fail twice, then succeed
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"summary": "test summary", "model": "gpt-4o-mini"}

            call_count = 0
            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise httpx.ConnectError("Connection refused")
                return mock_response_success

            mock_http_client.post.side_effect = side_effect
            mock_client_class.return_value = mock_http_client

            result = await client.generate_summary("test query", [{"text": "test", "document_id": "123", "chunk_index": 0}], "gpt-4o-mini")

            assert result is not None
            assert result["summary"] == "test summary"
            assert mock_http_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_list_models_retries_on_connection_error(self) -> None:
        """Test that list_models retries on connection errors."""
        client = GeneratorClient("http://localhost:8002")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_http_client = AsyncMock()
            mock_http_client.__aenter__.return_value = mock_http_client
            mock_http_client.__aexit__.return_value = None
            mock_http_client.get.side_effect = httpx.ConnectError("Connection refused")
            mock_client_class.return_value = mock_http_client

            with pytest.raises(RetryError):
                await client.list_models()

            assert mock_http_client.get.call_count == 3
