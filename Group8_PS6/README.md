# MATLAB Troubleshooting Assistant (Agentic AI, MCP-Powered)

## Overview

This project provides a developer-focused, AI-assisted troubleshooting system for MATLAB. It is built with a model-driven, agentic architecture that allows users to query, generate, and execute MATLAB code through a programmatic interface powered by large language models (LLMs).

The system eliminates the limitations of standard retrieval-based solutions by introducing state-aware interactions and runtime code execution. Its modular structure is built for reliability, traceability, and extensibility across debugging, automation, and intelligent assistant workflows.

## Problem Statement

MATLAB's advanced computing features make it indispensable in engineering and scientific workflows. However, the complexity of its toolchains, syntax, and runtime behavior presents significant challenges when users encounter errors or inefficiencies.

This system addresses that challenge by combining:

- An agentic architecture capable of multi-step task decomposition.
- Live MATLAB code generation and execution via a secure API layer.
- Contextual understanding powered by language models and structured knowledge bases.

The result is an interface that can answer MATLAB-related questions, propose and run solutions, and return actionable feedback in real time.

## Solution Architecture

![WhatsApp Image 2025-05-04 at 2 32 55 PM](https://github.com/user-attachments/assets/9fb60883-00e5-41f6-8a5d-9bdda9686ed4)

This implementation is composed of two core components:

### MCP Client ([Cherry Studio Fork](https://github.com/Kappuccino111/cherry-studio))

A custom fork of Cherry Studio providing:

- Integration with structured knowledge sources.
- Support for model-context protocol communication.
- Runtime tool injection, agent orchestration, and visualization.
- Configurable JSON-based setup for agent profiles and execution hooks.

### MCP Server (this repository)

Built using components from modelcontextprotocol.io:

- Exposes MATLAB functionality via HTTP/2.
- Wraps a local MATLAB runtime and manages execution state.
- Returns structured outputs and trace logs for verification.
- Written in Python and designed for local or secured network deployment.

## Getting Started

Prerequisites:
- We recommend using [uv](https://astral.sh/blog/uv) to manage your Python projects.
- MATLAB R2024a (or newer)
- Node.js (LTS version)
- Python 3.10+

### 1. Clone and Prepare the Repository

```bash
git clone https://github.com/your-org/matlab-mcp.git
cd matlab-mcp
```

### 2. Install Python Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure the System

Edit the file:

```
/Users/akarshankapoor/Desktop/matlab-mcp/claude_desktop_config_example.json
```

Ensure all paths are absolute and correspond to your environment, including:

- MATLAB executable path
- MCP server URL
- Knowledge base and tool paths

### 4. Start the MCP Server

Run the server using:

```bash
MATLAB_PATH=/Applications/MATLAB_R2024a.app uv run mcp dev matlab_server.py
```

This initializes the MATLAB runtime and begins listening for requests via HTTP/2.

### 5. Configure Cherry Studio

- Log into your Cherry Studio environment.
- Import the provided configuration file.
- Add the MCP server endpoint under tool definitions.
- Enable the Knowledge Base and dynamic routing if applicable.

### 6. Connect a Language Model

The system supports interaction with any LLM via API or open interface:

- OpenAI GPT series
- Anthropic Claude
- Local models (e.g., Mistral, LLaMA via vLLM, llama.cpp)
- Custom or fine-tuned LLMs using standard HTTP interfaces

## Example Use Cases

- Diagnose and correct runtime errors in MATLAB scripts.
- Automatically vectorize or optimize inefficient code.
- Generate and execute analysis pipelines from natural language descriptions.
- Visualize output of parameterized simulations via automated plots.

## Security Considerations

The system assumes a trusted runtime environment. If used in production or externally exposed:

- Ensure strict sanitization of code inputs.
- Run MATLAB in an isolated execution context or container.
- Use authenticated, rate-limited endpoints for model and server access.

## Why Not Use Standard RAG?

RAG systems fall short in this domain for three reasons:

1. MATLAB’s functionality is highly stateful.
2. Documentation-based retrieval cannot resolve runtime behavior.
3. Real-time troubleshooting requires execution feedback loops.

This system addresses those gaps through a direct MATLAB integration, runtime API access, and an agentic framework capable of multi-step reasoning.

## License

This project is released under the MIT License. See `LICENSE` for details.

## Contribution Guidelines

- Follow PEP8 and use Black for formatting.
- Write self-contained pull requests with clear commit history.
- Include type hints and docstrings for all new code.
- Use absolute paths or environment variables in all config files.
- For feature extensions, open a discussion issue prior to submitting code.

## Demo
The demo can be found on this link - https://youtu.be/LfPqlaGkw00


