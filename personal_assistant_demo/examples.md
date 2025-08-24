# Personal Assistant Demo - Example Interactions

This document provides example interactions you can try with the Personal Assistant Demo to showcase its capabilities.

## Quick Start Examples

### Basic Queries
```bash
# Simple time query
nat run --config_file configs/config.yml --input "What time is it?"

# Date information
nat run --config_file configs/config.yml --input "What's today's date?"

# Simple calculation
nat run --config_file configs/config.yml --input "What's 25 plus 37?"
```

## Weather Examples

### Basic Weather Queries
```bash
# Current weather
nat run --config_file configs/config.yml --input "What's the weather like in New York?"

# Weather condition check
nat run --config_file configs/config.yml --input "Is it raining in London?"

# Multiple cities
nat run --config_file configs/config.yml --input "What's the weather in Tokyo and Paris?"
```

### Weather-based Decision Making
```bash
# Complex weather query
nat run --config_file configs/config.yml --input "What's the weather in San Francisco and should I bring an umbrella?"

# Temperature comparison
nat run --config_file configs/config.yml --input "Is it warmer in Miami or Seattle right now?"
```

## Task Management Examples

### Basic Task Operations
```bash
# Add a task
nat run --config_file configs/config.yml --input "Add a task to buy groceries"

# List tasks
nat run --config_file configs/config.yml --input "Show me all my tasks"

# Complete a task
nat run --config_file configs/config.yml --input "Mark the grocery task as completed"

# Delete a task
nat run --config_file configs/config.yml --input "Delete task number 1"
```

### Advanced Task Management
```bash
# Multiple task operations
nat run --config_file configs/config.yml --input "Add a task to call mom, then show me all my tasks"

# Conditional task creation
nat run --config_file configs/config.yml --input "If it's going to rain in Boston tomorrow, add a task to bring an umbrella"

# Task completion by description
nat run --config_file configs/config.yml --input "Complete the task about calling mom"
```

## Calculator Examples

### Basic Math Operations
```bash
# Addition
nat run --config_file configs/config.yml --input "Add 15 and 28"

# Subtraction
nat run --config_file configs/config.yml --input "What's 100 minus 37?"

# Multiplication
nat run --config_file configs/config.yml --input "Multiply 8 by 9"

# Division
nat run --config_file configs/config.yml --input "Divide 144 by 12"
```

### Advanced Calculations
```bash
# Percentage calculations
nat run --config_file configs/config.yml --input "What's 20% of 150?"

# Multiple operations
nat run --config_file configs/config.yml --input "Add 10, 20, and 30, then multiply by 2"

# Real-world calculations
nat run --config_file configs/config.yml --input "If I have $100 and spend 25%, how much do I have left?"
```

## Date and Time Examples

### Time Information
```bash
# Current time
nat run --config_file configs/config.yml --input "What time is it right now?"

# Time calculations
nat run --config_file configs/config.yml --input "What time will it be in 3 hours?"

# Past time
nat run --config_file configs/config.yml --input "What time was it 2 hours ago?"
```

### Date Information
```bash
# Current date
nat run --config_file configs/config.yml --input "What's today's date?"

# Day of week
nat run --config_file configs/config.yml --input "What day of the week is it?"

# Timezone info
nat run --config_file configs/config.yml --input "What timezone am I in?"
```

## Complex Multi-Step Examples

### Weather + Tasks
```bash
# Weather-based task creation
nat run --config_file configs/config.yml --input "Check the weather in Chicago and if it's going to rain, add a task to pack an umbrella"

# Multiple city weather with task
nat run --config_file configs/config.yml --input "What's the weather in New York and Los Angeles, then add a task to check flight status"
```

### Calculations + Tasks
```bash
# Calculate and create task
nat run --config_file configs/config.yml --input "Calculate 20% of my $500 budget and create a task to save that amount"

# Time-based task
nat run --config_file configs/config.yml --input "What time will it be in 4 hours and add a task to call the doctor at that time"
```

### Complex Planning
```bash
# Multi-step planning
nat run --config_file configs/config.yml --input "What's the weather in Seattle, what time is it there, and create a task to call my friend if it's after 9 AM"

# Budget and task management
nat run --config_file configs/config.yml --input "Calculate 15% of 200, then create a task to transfer that amount to savings, then show me all my tasks"
```

## Interactive Mode Examples

For a more interactive experience, start the server:

```bash
nat serve --config_file configs/config.yml
```

Then open your browser to `http://localhost:8000` and try these conversational examples:

### Natural Conversation Flow
1. "Hi! What can you help me with?"
2. "What's the weather like today in San Francisco?"
3. "That sounds nice. What time is it there?"
4. "Great! Can you add a task for me to call my friend in SF?"
5. "Now show me all my tasks"
6. "Perfect! What's 15% of 120?"

### Task Management Conversation
1. "I need help organizing my day"
2. "Add a task to buy groceries"
3. "Also add a task to call the dentist"
4. "And one more - pick up dry cleaning"
5. "Show me all my tasks"
6. "I finished buying groceries, mark that as done"
7. "Now show me what's left to do"

### Planning Assistant Conversation
1. "I'm planning a trip to New York tomorrow"
2. "What's the weather going to be like there?"
3. "Should I pack an umbrella?"
4. "What time is it in New York right now?"
5. "Add a task to pack weather-appropriate clothes"
6. "Also calculate 20% of $300 for my tip budget"
7. "Create a task to set aside that tip money"

## Error Handling Examples

These examples show how the assistant handles various error conditions:

```bash
# Missing API key
nat run --config_file configs/config.yml --input "What's the weather in Paris?" 
# (without OPENWEATHERMAP_API_KEY set)

# Invalid calculations
nat run --config_file configs/config.yml --input "Divide 10 by 0"

# Non-existent tasks
nat run --config_file configs/config.yml --input "Complete task number 999"

# Invalid city names
nat run --config_file configs/config.yml --input "What's the weather in Nonexistentville?"
```

## Performance Testing

Test the agent's ability to handle complex, multi-step reasoning:

```bash
# Complex multi-step query
nat run --config_file configs/config.yml --input "What's the weather in Boston, calculate 25% of 400, add a task to save that amount if the weather is nice, then tell me what time it will be in 6 hours"

# Conditional logic
nat run --config_file configs/config.yml --input "If it's currently after 2 PM, add a task to call the bank, otherwise add a task to wait until after 2 PM to call"

# Multiple calculations
nat run --config_file configs/config.yml --input "Calculate 15% of 200, then add that to 50, then multiply by 2, and create a task to budget that final amount"
```

## Tips for Best Results

1. **Be specific**: "What's the weather in San Francisco?" works better than "How's the weather?"

2. **Use natural language**: The agent understands conversational requests like "Add a task to..." or "What's 20% of..."

3. **Combine operations**: You can ask for multiple things in one query: "What time is it and what's the weather in NYC?"

4. **Check your API keys**: Make sure your `.env` file has the correct API keys for full functionality

5. **Use the interactive mode**: `nat serve` provides a better experience for longer conversations

6. **Try different phrasings**: The agent can understand various ways of asking the same thing
