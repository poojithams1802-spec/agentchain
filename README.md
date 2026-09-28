# AgentChain

Adaptive Attack-Chain Discovery in Agentic AI Systems: A Knowledge-Guided Red-Teaming Framework

## Project Components

### Frontend & Visualization

The frontend provides the research dashboard and visualization interface.

It includes:

- Dashboard
- New Experiment
- Experiment Details
- Live Logs
- Findings
- Attack Chain Explorer
- Analytics
- Experiment History

The frontend is built with React and Vite.

### Security Sandbox

The sandbox provides a controlled environment for testing security weaknesses in an agentic AI system.

#### Agent

The toy agent manages tools and permissions.

#### Tools

- Search Tool
- File Tool
- Memory Tool

#### State

The agent maintains:

- Memory
- Action history
- Current test user

#### Security

The sandbox uses an explicit permission system to control tool access.

The sandbox is intentionally isolated and uses controlled data and deterministic tool behavior. It does not interact with real external systems.

## Frontend Setup

```bash
npm install
npm run dev
