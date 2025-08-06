"""A2A Protocol Client for communicating with A2A agents"""

import httpx
import structlog
from typing import Dict, Any, Optional
from uuid import uuid4
import json

logger = structlog.get_logger(__name__)


class A2AProtocolClient:
    """Client for communicating with A2A protocol agents"""
    
    def __init__(self, timeout: float = 5.0):
        """Initialize A2A client with timeout settings"""
        self.timeout = timeout
        
    async def send_query(self, endpoint: str, query: str) -> Dict[str, Any]:
        """
        Send a query to an A2A agent and return the response
        
        Args:
            endpoint: The base URL of the A2A agent (e.g., "http://a2a-math-agent:8002")
            query: The user's query text
            
        Returns:
            Dictionary containing the agent's response
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # First, get the agent card to understand the agent's capabilities
                agent_card_url = f"{endpoint}/.well-known/agent-card.json"
                
                logger.debug(
                    "Fetching A2A agent card",
                    url=agent_card_url
                )
                
                try:
                    card_response = await client.get(agent_card_url)
                    if card_response.status_code == 200:
                        agent_card = card_response.json()
                        logger.debug(
                            "Got A2A agent card",
                            agent_name=agent_card.get('name'),
                            skills=len(agent_card.get('skills', []))
                        )
                except Exception as e:
                    logger.warning(
                        "Failed to fetch agent card, continuing anyway",
                        error=str(e)
                    )
                
                # Prepare the message payload according to A2A protocol
                message_id = uuid4().hex
                message_payload = {
                    "jsonrpc": "2.0",
                    "method": "message/send",
                    "params": {
                        "message": {
                            "role": "user",
                            "parts": [
                                {
                                    "kind": "text",
                                    "text": query
                                }
                            ],
                            "messageId": message_id
                        }
                    },
                    "id": message_id
                }
                
                logger.debug(
                    "Sending A2A message",
                    endpoint=endpoint,
                    message_id=message_id,
                    query=query[:100]  # Log first 100 chars of query
                )
                
                # Send the message to the A2A agent
                response = await client.post(
                    f"{endpoint}/",  # A2A agents use root endpoint for JSON-RPC
                    json=message_payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(
                        "A2A agent returned non-200 status",
                        status_code=response.status_code,
                        response_text=response.text[:500]
                    )
                    return {
                        "error": f"Agent returned status {response.status_code}",
                        "text": f"Failed to get response from A2A agent (status: {response.status_code})"
                    }
                
                # Parse the JSON-RPC response
                response_data = response.json()
                
                logger.debug(
                    "Received A2A response",
                    has_result="result" in response_data,
                    has_error="error" in response_data
                )
                
                # Handle JSON-RPC error responses
                if "error" in response_data:
                    error_info = response_data["error"]
                    logger.error(
                        "A2A agent returned error",
                        error_code=error_info.get("code"),
                        error_message=error_info.get("message")
                    )
                    return {
                        "error": error_info.get("message", "Unknown error"),
                        "text": f"Error from agent: {error_info.get('message', 'Unknown error')}"
                    }
                
                # Extract the result from successful response
                if "result" in response_data:
                    result = response_data["result"]
                    
                    # Handle different response formats
                    if isinstance(result, dict):
                        # Check for message structure
                        if "message" in result:
                            message = result["message"]
                            # Extract text from message parts
                            text_content = self._extract_text_from_message(message)
                            return {
                                "text": text_content,
                                "message_id": message.get("messageId"),
                                "role": message.get("role", "agent"),
                                "raw_result": result
                            }
                        # Direct text response
                        elif "text" in result:
                            return {
                                "text": result["text"],
                                "raw_result": result
                            }
                        # Unknown structure, return as-is
                        else:
                            return {
                                "text": json.dumps(result),
                                "raw_result": result
                            }
                    # Simple string response
                    elif isinstance(result, str):
                        return {
                            "text": result,
                            "raw_result": result
                        }
                    else:
                        return {
                            "text": str(result),
                            "raw_result": result
                        }
                
                # Fallback if no result field
                logger.warning(
                    "A2A response missing 'result' field",
                    response_keys=list(response_data.keys())
                )
                return {
                    "text": "No result in response",
                    "raw_response": response_data
                }
                
        except httpx.TimeoutException:
            logger.error(
                "A2A request timed out",
                endpoint=endpoint,
                timeout=self.timeout
            )
            return {
                "error": "Request timed out",
                "text": f"Request to A2A agent timed out after {self.timeout} seconds"
            }
        except httpx.RequestError as e:
            logger.error(
                "A2A request failed",
                endpoint=endpoint,
                error=str(e)
            )
            return {
                "error": str(e),
                "text": f"Failed to connect to A2A agent: {str(e)}"
            }
        except Exception as e:
            logger.error(
                "Unexpected error in A2A client",
                endpoint=endpoint,
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                "error": str(e),
                "text": f"Unexpected error: {str(e)}"
            }
    
    def _extract_text_from_message(self, message: Dict[str, Any]) -> str:
        """
        Extract text content from an A2A message structure
        
        Args:
            message: A2A message dictionary with parts
            
        Returns:
            Extracted text content
        """
        parts = message.get("parts", [])
        text_parts = []
        
        for part in parts:
            if isinstance(part, dict) and part.get("kind") == "text":
                text_parts.append(part.get("text", ""))
        
        return " ".join(text_parts) if text_parts else "No text content in message"