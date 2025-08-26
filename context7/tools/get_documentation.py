from collections.abc import Generator
from typing import Any
import requests

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class GetDocumentationTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        library_id = tool_parameters.get("library_id", "").strip()
        
        if not library_id:
            yield self.create_text_message("Library ID is required")
            return
        
        # Remove leading slash if present (Context7 search returns IDs with leading slash)
        if library_id.startswith('/'):
            library_id = library_id[1:]
            
        # Get optional parameters
        format_type = tool_parameters.get("format", "txt")
        topic = tool_parameters.get("topic", "").strip()
        tokens = tool_parameters.get("tokens", 10000)
        
        # Validate tokens parameter
        try:
            tokens = int(tokens)
            if tokens <= 0:
                tokens = 10000
            elif tokens > 50000:
                tokens = 50000
        except (ValueError, TypeError):
            tokens = 10000
        
        try:
            # Get API key from credentials (provided during plugin installation)
            api_key = self.runtime.credentials.get("api_key")
            
            if not api_key:
                yield self.create_text_message("Context7 API key not configured. Please reinstall the plugin and provide your API key.")
                return
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare URL and parameters
            url = f"https://context7.com/api/v1/{library_id}"
            params = {
                "type": format_type,
                "tokens": tokens
            }
            
            # Add topic filter if provided
            if topic:
                params["topic"] = topic
            
            # Make documentation request
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=60  # Longer timeout for potentially large responses
            )
            
            if response.status_code == 401:
                yield self.create_text_message("Invalid API key. Please check your Context7 credentials.")
                return
            elif response.status_code == 403:
                yield self.create_text_message("API key does not have required permissions.")
                return
            elif response.status_code == 404:
                yield self.create_text_message(f"Library '{library_id}' not found. Please verify the library ID using the Search Libraries tool.")
                return
            elif response.status_code != 200:
                yield self.create_text_message(f"Documentation request failed with status {response.status_code}: {response.text}")
                return
            
            # Handle response based on format
            if format_type == "json":
                try:
                    documentation_data = response.json()
                    yield self.create_text_message(f"Retrieved documentation for library '{library_id}' in JSON format")
                    yield self.create_json_message({
                        "library_id": library_id,
                        "format": format_type,
                        "topic": topic if topic else "all",
                        "token_limit": tokens,
                        "documentation": documentation_data
                    })
                except ValueError as e:
                    yield self.create_text_message(f"Failed to parse JSON response: {str(e)}")
                    return
            else:
                # Text format
                documentation_text = response.text
                
                if not documentation_text.strip():
                    yield self.create_text_message(f"No documentation found for library '{library_id}'")
                    return
                
                # Create summary message
                summary = f"Documentation for '{library_id}'"
                if topic:
                    summary += f" (topic: {topic})"
                summary += f"\nToken limit: {tokens:,}"
                summary += f"\nFormat: {format_type}"
                summary += "\n" + "="*50 + "\n\n"
                
                full_response = summary + documentation_text
                
                yield self.create_text_message(full_response)
                yield self.create_json_message({
                    "library_id": library_id,
                    "format": format_type,
                    "topic": topic if topic else "all",
                    "token_limit": tokens,
                    "documentation_length": len(documentation_text),
                    "summary": f"Retrieved {len(documentation_text):,} characters of documentation for {library_id}"
                })
                
        except requests.exceptions.RequestException as e:
            yield self.create_text_message(f"Failed to connect to Context7 API: {str(e)}")
        except Exception as e:
            yield self.create_text_message(f"Documentation retrieval failed: {str(e)}")
