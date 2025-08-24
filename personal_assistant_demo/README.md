<!--
SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Personal Assistant Agent Demo

A comprehensive demonstration of the NeMo Agent Toolkit featuring a personal assistant agent that can help with daily tasks. This demo showcases the toolkit's key capabilities including custom function registration, multi-step reasoning, and framework-agnostic design.

## Table of Contents

- [Key Features](#key-features)
- [Installation and Setup](#installation-and-setup)
- [Running the Demo](#running-the-demo)
- [Example Interactions](#example-interactions)
- [Architecture Overview](#architecture-overview)
- [Customization](#customization)

---

## Key Features

- **Task Management:** Create, list, and complete personal tasks with persistent storage
- **Mathematical Operations:** Perform basic calculations (add, subtract, multiply, divide)
- **Date/Time Information:** Get current date, time, and timezone information
- **Weather Information:** Get current weather conditions for any city (requires API key)
- **Multi-step Reasoning:** Uses ReAct agent to break down complex queries into sequential tool calls
- **Custom Function Registration:** Demonstrates the NeMo Agent Toolkit plugin system
- **YAML-based Configuration:** Fully configurable workflow through simple YAML files
- **Persistent Storage:** Tasks are stored locally and persist between sessions

---

## Installation and Setup

### Prerequisites

1. Python 3.11 or 3.12 installed
2. NeMo Agent Toolkit development environment set up
3. API keys for NVIDIA and OpenWeatherMap services

### Install this Demo

From the root directory of this demo, run:

```bash
# Using uv (recommended - faster)
uv pip install -e .

# Or using pip
pip install -e .
```

### Set Up API Keys

You'll need the following API keys:

1. **NVIDIA API Key** (required): Get from [build.nvidia.com](https://build.nvidia.com/)
2. **OpenWeatherMap API Key** (optional): Get from [openweathermap.org](https://openweathermap.org/api)

```bash
export NVIDIA_API_KEY=<YOUR_NVIDIA_API_KEY>
export OPENWEATHERMAP_API_KEY=<YOUR_OPENWEATHERMAP_API_KEY>  # Optional
```

---

## Running the Demo

### Basic Usage

Run the personal assistant with a simple query:

```bash
nat run --config_file configs/config.yml --input "What time is it and add a task to review the demo?"
```

### Interactive Mode

For a more interactive experience, you can use the NeMo Agent Toolkit UI:

```bash
nat serve --config_file configs/config.yml
```

Then open your browser to `http://localhost:8000` to interact with the assistant through a web interface.

---

## Example Interactions

Here are some example queries you can try:

### Weather Queries
- "What's the weather like in San Francisco?"
- "Is it raining in London right now?"
- "What's the temperature in Tokyo?"

### Task Management
- "Add a task to buy groceries"
- "List all my tasks"
- "Mark the grocery task as completed"
- "Create a task to call mom tomorrow"

### Calculations
- "What's 15 multiplied by 8?"
- "Calculate 100 divided by 4"
- "Add 25 and 37"

### Date/Time
- "What time is it?"
- "What's today's date?"
- "What timezone am I in?"

### Complex Multi-step Queries
- "What's the weather in Paris and add a task to pack an umbrella if it's going to rain"
- "Calculate 20% of 150 and create a task to save that amount"
- "What time is it and how much is 8 hours from now?"

---

## Architecture Overview

This demo follows NeMo Agent Toolkit best practices:

```
personal_assistant_demo/
├── src/
│   └── personal_assistant/
│       ├── __init__.py
│       ├── register.py          # Custom function registration
│       └── tools/
│           ├── weather.py       # Weather API integration
│           ├── tasks.py         # Task management functions
│           ├── calculator.py    # Mathematical operations
│           └── datetime_info.py # Date/time utilities
├── configs/
│   └── config.yml              # Main workflow configuration
├── tests/
│   ├── test_weather.py
│   ├── test_tasks.py
│   └── test_calculator.py
├── data/
│   └── tasks.json              # Persistent task storage
├── pyproject.toml              # Package configuration
└── README.md
```

### Key Components

1. **Custom Functions**: Each tool is implemented as a custom function following NAT conventions
2. **ReAct Agent**: Uses reasoning and action cycles to handle complex queries
3. **Plugin System**: Functions are registered through the NAT plugin system
4. **Configuration**: All behavior is controlled through YAML configuration
5. **Persistence**: Tasks are stored in JSON format for persistence between sessions

---

## Customization

### Adding New Tools

To add a new tool:

1. Create a new function in `src/personal_assistant/tools/`
2. Register it in `src/personal_assistant/register.py`
3. Add it to the workflow configuration in `configs/config.yml`

### Modifying the Agent

You can customize the agent behavior by:

- Changing the LLM model in the configuration
- Adjusting the agent's system prompt
- Adding or removing tools from the workflow
- Modifying the agent type (ReAct, Tool Calling, etc.)

### Configuration Options

The `configs/config.yml` file allows you to:

- Switch between different LLM providers (NVIDIA NIM, OpenAI, etc.)
- Adjust model parameters (temperature, max tokens)
- Enable/disable specific tools
- Configure tool-specific settings

---

## Troubleshooting

### Common Issues

1. **API Key Issues**: Ensure your NVIDIA_API_KEY is set correctly
2. **Weather Not Working**: Check your OPENWEATHERMAP_API_KEY or disable weather tools
3. **Task Persistence**: Ensure the `data/` directory is writable
4. **Import Errors**: Make sure you've installed the package with `pip install -e .`

### Getting Help

- Check the [NeMo Agent Toolkit Documentation](https://docs.nvidia.com/nemo/agent-toolkit/latest)
- Review the [Troubleshooting Guide](https://docs.nvidia.com/nemo/agent-toolkit/latest/troubleshooting.html)
- File issues on the [GitHub Repository](https://github.com/NVIDIA/NeMo-Agent-Toolkit/issues)

---

## License

This demo is licensed under the Apache License 2.0. See the LICENSE file for details.
