# Thin Facade Pattern for Engine and Server Surfaces

`engine.py` and `server.py` are thin re-export facades with zero business logic. All actual processing lives in `engine_*.py` and `server_tools_*.py` modules. This keeps the public import surface stable while allowing internal refactoring without breaking callers.
