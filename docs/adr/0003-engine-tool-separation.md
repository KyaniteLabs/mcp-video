# Engine/Tool Separation

MCP tool handlers (`server_tools_*.py`) validate inputs and format results; they do not contain business logic. Business logic lives in engine modules (`engine_*.py`, `effects_engine/`, `audio_engine/`, `ai_engine/`). This creates a clean seam: tools can be reimplemented for a different transport (CLI, HTTP, gRPC) without touching engines.
