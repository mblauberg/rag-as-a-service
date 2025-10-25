"""Tests for HTTP embedding service adapter."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.infrastructure.services.embedding_service import HTTPEmbeddingService
from app.core.exceptions import EmbeddingServiceError


class TestHTTPEmbeddingService:
    """Test suite for HTTPEmbeddingService adapter."""

    @pytest.fixture
    def embedder_url(self):
        """Fixture for embedder service URL."""
        return "http://localhost:8001"

    @pytest.fixture
    def service(self, embedder_url):
        """Fixture for HTTPEmbeddingService instance."""
        return HTTPEmbeddingService(embedder_url=embedder_url)

    @pytest.fixture
    def mock_response(self):
        """Fixture for mocked HTTP response."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "embeddings": [
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6]
            ]
        }
        return response

    @pytest.mark.asyncio
    async def test_generate_embeddings_success(self, service, embedder_url, mock_response):
        """Test successful embedding generation."""
        texts = ["hello world", "test document"]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await service.generate_embeddings(texts)

            # Verify HTTP call
            mock_client.post.assert_called_once_with(
                f"{embedder_url}/embed",
                json={"texts": texts},
                timeout=30.0
            )

            # Verify result
            assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
            assert len(result) == 2
            assert all(isinstance(embedding, list) for embedding in result)
            assert all(isinstance(val, float) for embedding in result for val in embedding)

    @pytest.mark.asyncio
    async def test_generate_embeddings_network_error(self, service):
        """Test handling of network errors."""
        texts = ["hello world"]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            mock_client_class.return_value = mock_client

            with pytest.raises(EmbeddingServiceError) as exc_info:
                await service.generate_embeddings(texts)

            assert "Failed to connect to embedding service" in str(exc_info.value)
            assert exc_info.value.original_error is not None

    @pytest.mark.asyncio
    async def test_generate_embeddings_timeout(self, service):
        """Test handling of timeout errors."""
        texts = ["hello world"]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
            mock_client_class.return_value = mock_client

            with pytest.raises(EmbeddingServiceError) as exc_info:
                await service.generate_embeddings(texts)

            assert "Embedding service request timed out" in str(exc_info.value)
            assert exc_info.value.original_error is not None

    @pytest.mark.asyncio
    async def test_generate_embeddings_http_error(self, service):
        """Test handling of HTTP errors (4xx, 5xx)."""
        texts = ["hello world"]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            # Create a proper HTTPStatusError
            request = httpx.Request("POST", "http://localhost:8001/embed")
            response = httpx.Response(500, request=request)
            mock_client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
                "Server error", request=request, response=response
            ))
            mock_client_class.return_value = mock_client

            with pytest.raises(EmbeddingServiceError) as exc_info:
                await service.generate_embeddings(texts)

            assert "Embedding service returned error" in str(exc_info.value)
            assert exc_info.value.original_error is not None

    @pytest.mark.asyncio
    async def test_generate_embeddings_invalid_response_structure(self, service):
        """Test handling of invalid response structure."""
        texts = ["hello world"]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            # Response missing 'embeddings' key
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with pytest.raises(EmbeddingServiceError) as exc_info:
                await service.generate_embeddings(texts)

            assert "Invalid response format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_embeddings_mismatched_count(self, service):
        """Test handling of response with wrong number of embeddings."""
        texts = ["hello world", "test document"]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            # Response with only one embedding for two texts
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [[0.1, 0.2, 0.3]]
            }
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with pytest.raises(EmbeddingServiceError) as exc_info:
                await service.generate_embeddings(texts)

            assert "Expected 2 embeddings but got 1" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_embeddings_invalid_json(self, service):
        """Test handling of invalid JSON response."""
        texts = ["hello world"]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            # Response that raises JSONDecodeError
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with pytest.raises(EmbeddingServiceError) as exc_info:
                await service.generate_embeddings(texts)

            assert "Failed to parse embedding service response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_embeddings_empty_input(self, service):
        """Test handling of empty input list."""
        texts = []

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"embeddings": []}
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await service.generate_embeddings(texts)

            assert result == []
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_client_context_manager(self, service):
        """Test that httpx client is properly used as context manager."""
        texts = ["hello world"]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await service.generate_embeddings(texts)

            # Verify context manager was used
            mock_client.__aenter__.assert_called_once()
            mock_client.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_timeout_configuration(self, service, embedder_url):
        """Test that timeout is properly configured."""
        texts = ["hello world"]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await service.generate_embeddings(texts)

            # Verify timeout is set to 30 seconds
            call_args = mock_client.post.call_args
            assert call_args[1]["timeout"] == 30.0
