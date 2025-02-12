# LLM_agent
The agent at the center of the system. Interacting with the client, the database and the LLMs

# Usage
- To run in development: `python api.py`
- To run in production: `python -m waitress --listen=0.0.0.0:5124 api:app`