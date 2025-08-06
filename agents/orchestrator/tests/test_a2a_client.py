"""Tests for A2A protocol client functionality."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx
import json

from orchestrator.protocols.a2a_client import A2AProtocolClient


class TestA2AProtocolClient:
    """Test suite for A2A protocol client."""

    def test_client_initialization(self):
        """Test A2A client initialization."""
        client = A2AProtocolClient()
        assert client.timeout == 5.0  # default timeout
        
        client_with_timeout = A2AProtocolClient(timeout=15.0)
        assert client_with_timeout.timeout == 15.0

    @pytest.mark.asyncio
    async def test_send_query_success(self):
        """Test successful query sending to A2A agent."""
        client = A2AProtocolClient(timeout=5.0)
        endpoint = "http://test-agent:8002"
        query = "What is 2 + 2?"
        
        expected_result = {
            "message": {
                "role": "agent",
                "parts": [{"kind": "text", "text": "🧮 Calc: 2.0 + 2.0 = 4.0"}],
                "messageId": "response_123"
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None
            
            # Mock agent card response (GET request)
            mock_card_response = Mock()
            mock_card_response.status_code = 200
            mock_card_response.json.return_value = {"name": "Test Agent", "skills": []}
            mock_client.get.return_value = mock_card_response
            
            # Mock the main POST response
            mock_post_response = Mock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                "jsonrpc": "2.0",
                "result": expected_result,
                "id": "test_id"
            }
            mock_client.post.return_value = mock_post_response
            
            result = await client.send_query(endpoint, query)
            
            # Verify the result structure
            assert "text" in result
            assert "🧮 Calc: 2.0 + 2.0 = 4.0" in result["text"]
            assert "message_id" in result
            assert result["role"] == "agent"

    @pytest.mark.asyncio
    async def test_send_query_http_error(self):
        """Test handling of HTTP errors from A2A agent."""
        client = A2AProtocolClient(timeout=5.0)
        endpoint = "http://test-agent:8002"
        query = "Test query"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None
            
            # Mock agent card response (successful)
            mock_card_response = Mock()
            mock_card_response.status_code = 200
            mock_card_response.json.return_value = {"name": "Test Agent"}
            mock_client.get.return_value = mock_card_response
            
            # Mock 404 POST response
            mock_post_response = Mock()
            mock_post_response.status_code = 404
            mock_post_response.text = "Not Found"
            mock_client.post.return_value = mock_post_response
            
            result = await client.send_query(endpoint, query)
            
            # Should return error response
            assert "error" in result
            assert "404" in result["error"]
            assert "text" in result

    @pytest.mark.asyncio
    async def test_send_query_timeout(self):
        """Test handling of timeout errors."""
        client = A2AProtocolClient(timeout=5.0)
        endpoint = "http://test-agent:8002"
        query = "Test query"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None
            
            # Mock timeout on POST request
            mock_client.get.return_value = Mock(status_code=200, json=lambda: {})
            mock_client.post.side_effect = httpx.TimeoutException("Request timed out")
            
            result = await client.send_query(endpoint, query)
            
            # Should return timeout error response
            assert "error" in result
            assert "timed out" in result["error"].lower()
            assert "text" in result

    @pytest.mark.asyncio
    async def test_send_query_connection_error(self):
        """Test handling of connection errors."""
        client = A2AProtocolClient(timeout=5.0)
        endpoint = "http://unreachable-agent:8002"
        query = "Test query"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None
            
            # Mock connection error
            mock_client.get.side_effect = httpx.ConnectError("Connection failed")
            
            result = await client.send_query(endpoint, query)
            
            # Should return connection error response
            assert "error" in result
            assert "text" in result

    @pytest.mark.asyncio
    async def test_send_query_jsonrpc_error(self):
        """Test handling of JSON-RPC error responses."""
        client = A2AProtocolClient(timeout=5.0)
        endpoint = "http://test-agent:8002"
        query = "Test query"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None
            
            # Mock successful GET
            mock_client.get.return_value = Mock(status_code=200, json=lambda: {})
            
            # Mock JSON-RPC error response
            mock_post_response = Mock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request"
                },
                "id": "test_id"
            }
            mock_client.post.return_value = mock_post_response
            
            result = await client.send_query(endpoint, query)
            
            # Should return error response
            assert "error" in result
            assert "Invalid Request" in result["error"]
            assert "text" in result

    def test_extract_text_from_message(self):
        """Test text extraction from A2A message structure."""
        client = A2AProtocolClient()
        
        # Test with valid message structure
        message = {
            "parts": [
                {"kind": "text", "text": "Hello "},
                {"kind": "text", "text": "World!"}
            ]
        }
        
        result = client._extract_text_from_message(message)
        assert result == "Hello  World!"
        
        # Test with empty parts
        message_empty = {"parts": []}
        result_empty = client._extract_text_from_message(message_empty)
        assert result_empty == "No text content in message"
        
        # Test with non-text parts
        message_mixed = {
            "parts": [
                {"kind": "image", "url": "image.jpg"},
                {"kind": "text", "text": "Some text"}
            ]
        }
        result_mixed = client._extract_text_from_message(message_mixed)
        assert result_mixed == "Some text"

    @pytest.mark.asyncio
    async def test_send_query_with_string_result(self):
        """Test handling of simple string result from agent."""
        client = A2AProtocolClient(timeout=5.0)
        endpoint = "http://test-agent:8002"
        query = "Simple query"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None
            
            # Mock GET request
            mock_client.get.return_value = Mock(status_code=200, json=lambda: {})
            
            # Mock POST with string result
            mock_post_response = Mock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                "jsonrpc": "2.0",
                "result": "Simple string response",
                "id": "test_id"
            }
            mock_client.post.return_value = mock_post_response
            
            result = await client.send_query(endpoint, query)
            
            assert result["text"] == "Simple string response"
            assert result["raw_result"] == "Simple string response"

    @pytest.mark.asyncio 
    async def test_agent_card_fetch_failure(self):
        """Test that agent card fetch failure doesn't prevent query execution."""
        client = A2AProtocolClient(timeout=5.0)
        endpoint = "http://test-agent:8002"
        query = "Test query"
        
        expected_result = {"text": "Success despite card failure"}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None
            
            # Mock GET request failure (agent card)
            mock_client.get.side_effect = Exception("Card fetch failed")
            
            # Mock successful POST request
            mock_post_response = Mock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                "jsonrpc": "2.0",
                "result": expected_result,
                "id": "test_id"
            }
            mock_client.post.return_value = mock_post_response
            
            result = await client.send_query(endpoint, query)
            
            # Should succeed despite card fetch failure
            assert result["text"] == "Success despite card failure"