# Code Review Multi-Agent - Design Document

> Created: 2026/04/26 | Last Updated: 2026/04/27 | Status: **Implemented**

## 1. Project Overview

**Code Review Multi-Agent** is an AI-powered code review system that automatically analyzes GitHub Pull Requests using specialized agents for different review aspects.

## 2. Architecture Design

### 2.1 Multi-Agent Framework Choice

**LangGraph** was chosen over plain LangChain for:
- First-class support for Multi-Agent orchestration
- Built-in state management with reducers
- Conditional edges for fan-out/fan-in patterns
- Production-ready for agent workflows

### 2.2 Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Router Agent                           │
│  Classifies files: Security | Bug | Style | All             │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Security   │   │    Bug      │   │   Style     │
│   Agent     │   │   Agent     │   │   Agent     │
│             │   │             │   │             │
│ • SQL inj   │   │ • Null ptr  │   │ • Docs      │
│ • Secrets   │   │ • Div/zero  │   │ • Naming    │
│ • Path trav │   │ • Index OOB │   │ • Format    │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
              ┌─────────────────────┐
              │  Aggregator Agent  │
              │  • Combine results  │
              │  • Generate summary │
              └─────────────────────┘
```

### 2.3 State Management

LangGraph `TypedDict` with custom reducer for parallel node results:

```python
class ReviewState(TypedDict):
    pr_id: int
    repo_owner: str
    repo_name: str
    files: list
    routes: dict  # Router result
    agent_results: Annotated[dict, _merge_agent_results]  # Parallel merge
    review_comments: list
    overall_status: str
```

### 2.4 Data Flow

```
1. GitHub Webhook (PR opened/sync) → FastAPI /webhook
2. Parse PR files → Prepare file contents
3. Route Node → Classify files to agents
4. Agent Nodes (parallel) → Analyze code
5. Aggregate Node → Combine and summarize
6. Post Comments → GitHub PR Review API
```

## 3. Technology Stack

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| Agent Framework | LangGraph | Latest | Multi-Agent orchestration |
| LLM | MiniMax API | v1 | OpenAI-compatible, cost-effective |
| API Framework | FastAPI | Latest | Async, auto-docs |
| HTTP Client | httpx | Latest | Async, timeout support |
| Validation | Pydantic | Latest | Type safety |
| Testing | pytest | Latest | Standard Python testing |

## 4. Key Design Decisions

### 4.1 Phase 1: Single Agent → Phase 2: Multi-Agent

**Decision**: Start with single agent, evolve to multi-agent

**Rationale**:
- Phase 1 for quick MVP and webhook validation
- Phase 2 for specialized, higher-quality analysis
- LangGraph makes migration straightforward

### 4.2 GitHub Webhook → GitHub App (Future)

**Decision**: Phase 1 uses Webhook, Phase X upgrades to GitHub App

**Rationale**:
- Webhook: Quick setup, no OAuth flow
- GitHub App: Better permissions, events, no ngrok needed

### 4.3 State Merging Strategy

**Decision**: Custom reducer for parallel node results

```python
def _merge_agent_results(left: dict, right: dict) -> dict:
    """Merge agent_results without double-wrapping"""
    result = {}
    for key, value in chain(left.items(), right.items()):
        if key == "agent_results" and isinstance(value, dict):
            for agent_name, agent_data in value.items():
                if agent_name not in result:
                    result[agent_name] = agent_data
                elif isinstance(agent_data, list):
                    result[agent_name] = result.get(agent_name, []) + agent_data
        else:
            result[key] = value
    return result  # Return dict directly, not wrapped
```

### 4.4 HTTP Timeout & Retry

**Decision**: 30s timeout with 3 retries for all GitHub API calls

**Rationale**:
- GitHub API can be slow or rate-limited
- Prevents request hanging
- Exponential backoff via retries

## 5. Security Considerations

1. **Webhook Signature Verification**: Commented out for local testing
2. **GitHub Token**: Environment variable, never hardcoded
3. **LLM Output**: Validated via Pydantic models
4. **Comment Line Numbers**: Validated against file line count

## 6. Testing Strategy

- **Unit Tests**: Each agent, client method, schema validation
- **Integration Tests**: Workflow end-to-end (mocked LLM)
- **Manual Tests**: Real GitHub PR with test repository

## 7. Future Extensions

### Phase 3: Enhanced Features
- Summary report with markdown formatting
- Review dashboard/database
- Multiple repository support

### Phase 4: Advanced Analysis
- C++ static analysis (clang-tidy, cppcheck)
- ML-based issue classification
- Custom rule DSL

## 8. Performance Considerations

- **Parallel Execution**: 3 agents run concurrently via LangGraph Send
- **LLM Calls**: One call per file per agent
- **GitHub API**: Batched review comments in single request
