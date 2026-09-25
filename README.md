# AgentChain Security Sandbox

This module provides a controlled environment for testing
security weaknesses in an agentic AI system.

## Components

### Agent
The toy agent manages tools and permissions.

### Tools

- Search Tool
- File Tool
- Memory Tool

### State

The agent maintains:

- Memory
- Action history
- Current test user

### Security

The sandbox uses an explicit permission system
to control tool access.

## Safety

This sandbox is intentionally isolated and uses
controlled data and deterministic tool behavior.

It does not interact with real external systems.

## Current Status

Day 1:
- Sandbox foundation
- Toy agent
- Search tool
- File tool
- Memory tool
- Permission system

Day 2:
- Vulnerability scenarios