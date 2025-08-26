from collections.abc import Generator
from typing import Any
import requests

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class SearchLibrariesTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        query = tool_parameters.get("query", "").strip()
        
        if not query:
            yield self.create_text_message("Search query is required")
            return
            
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
            
            # Make search request
            response = requests.get(
                "https://context7.com/api/v1/search",
                headers=headers,
                params={"query": query},
                timeout=30
            )
            
            if response.status_code == 401:
                yield self.create_text_message("Invalid API key. Please check your Context7 credentials.")
                return
            elif response.status_code == 403:
                yield self.create_text_message("API key does not have required permissions.")
                return
            elif response.status_code != 200:
                yield self.create_text_message(f"Search request failed with status {response.status_code}: {response.text}")
                return
            
            # Parse response
            response_data = response.json()
            search_results = response_data.get('results', [])
            
            if not search_results or len(search_results) == 0:
                yield self.create_text_message(f"No libraries found matching '{query}'")
                return
            
            # Format results for display
            result_text = f"Found {len(search_results)} libraries matching '{query}':\n\n"
            
            for i, library in enumerate(search_results, 1):
                library_id = library.get('id', 'Unknown ID')
                title = library.get('title', 'Unknown Title')
                description = library.get('description', 'No description available')
                total_tokens = library.get('totalTokens', 0)
                trust_score = library.get('trustScore', 0)
                
                result_text += f"{i}. **{title}** (ID: `{library_id}`)\n"
                result_text += f"   {description}\n"
                result_text += f"   Tokens: {total_tokens:,} | Trust Score: {trust_score}\n\n"
            
            result_text += "Use the 'Get Documentation' tool with the library ID to retrieve documentation and code samples."
            
            # Return both text and JSON responses
            yield self.create_text_message(result_text)
            yield self.create_json_message({
                "query": query,
                "results_count": len(search_results),
                "libraries": search_results
            })
            
        except requests.exceptions.RequestException as e:
            yield self.create_text_message(f"Failed to connect to Context7 API: {str(e)}")
        except Exception as e:
            yield self.create_text_message(f"Search failed: {str(e)}")
