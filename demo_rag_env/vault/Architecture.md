# Deployment Architecture
The system runs as a Python backend server exposing a WebSocket API.
Clients like Obsidian connect to this server.
Data is stored in ChromaDB (vectors) and SQLite (metadata).
