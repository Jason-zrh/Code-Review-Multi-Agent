# Code Review Multi-Agent - Project Status

> Last Updated: 2026/04/27

## Project Overview

**Code Review Multi-Agent** is an AI-powered code review system that automatically analyzes GitHub Pull Requests using specialized agents for security, bug detection, and code style analysis.

## Current Status: Phase 1 & Phase 2 Completed ✅

## Completed Features

### Phase 1: Basic Integration (2026-04-26)

| Feature | Status | Description |
|---------|--------|-------------|
| Project Structure | ✅ | Clean layered architecture |
| Data Models | ✅ | Pydantic schemas for PR, ReviewComment, etc. |
| GitHub Webhook | ✅ | Receive and verify GitHub PR events |
| GitHub API Client | ✅ | Get PR files, post review comments |
| LLM Integration | ✅ | MiniMax API (OpenAI-compatible) |
| Single Agent Review | ✅ | Basic code analysis |

### Phase 2: Multi-Agent Architecture (2026-04-27)

| Feature | Status | Description |
|---------|--------|-------------|
| Router Agent | ✅ | Classifies files to appropriate agents |
| Security Agent | ✅ | Detects SQL injection, secrets, path traversal |
| Bug Agent | ✅ | Detects null pointers, division by zero, etc. |
| Style Agent | ✅ | Detects missing docs, bad naming |
| Aggregator Agent | ✅ | Combines results from all agents |
| Parallel Execution | ✅ | LangGraph Send API for fan-out |
| State Merging | ✅ | Custom reducer for parallel results |

### Bug Fixes Log

| Issue | Root Cause | Solution |
|-------|------------|----------|
| `'str' object has no attribute 'get'` | State merging returned nested dict | Merge results directly, not wrapped |
| HTTP Timeout on GitHub API | No timeout configured | Added 30s timeout + 3 retries |
| `state['routes']` is None | LangGraph state update timing | Default to all agents if routes missing |
| PR ID vs Number confusion | GitHub API uses different IDs | Use PR number for API calls |
| Commit SHA validation | "HEAD" not valid SHA | Get actual SHA from PR details |
| Empty file comments | GitHub API rejects comments on empty diffs | Skip files without valid patches |
| Line number overflow | LLM may generate invalid line numbers | Clamp line numbers to file range |

## Architecture

### Multi-Agent Workflow

```
GitHub PR Event → Route → [Security | Bug | Style] (parallel)
                           ↓
                       Aggregate → Post Comments → GitHub PR
```

### Key Technologies

- **LangGraph**: Multi-agent orchestration with state machines
- **FastAPI**: REST API framework
- **httpx**: Async HTTP client with timeout/retry
- **Pydantic**: Data validation and serialization
- **MiniMax API**: LLM for code analysis

## File Structure Summary

```
src/
├── main.py                    # Entry point
├── models/schemas.py           # 5 models: PullRequest, FileChange, ReviewComment, RouteResult, ReviewResult
├── github/
│   ├── webhook.py              # Signature verification, event parsing
│   └── client.py               # GitHub REST API (with retry)
├── coordinator/
│   └── workflow.py             # LangGraph StateGraph (Phase 2)
├── agents/
│   ├── router_agent.py         # File classification (Phase 2)
│   ├── security_agent.py       # Security vulnerability detection (Phase 2)
│   ├── bug_agent.py            # Bug detection (Phase 2)
│   ├── style_agent.py          # Code style analysis (Phase 2)
│   ├── aggregator_agent.py     # Result aggregation (Phase 2)
│   └── code_reviewer.py        # Legacy Phase 1 agent (deprecated)
└── api/routes.py               # /webhook endpoint
```

## Testing

### Test Coverage

| Test File | Coverage |
|-----------|----------|
| test_workflow.py | Workflow state management, routing |
| test_router_agent.py | File classification logic |
| test_specialized_agents.py | Security/Bug/Style agents |
| test_aggregator_agent.py | Result aggregation |
| test_github_client.py | API client methods |
| test_schemas.py | Pydantic model validation |
| test_routes.py | API endpoint behavior |

### Test Results (Latest)

```
✅ All Phase 2 agents tested successfully
✅ Workflow parallel execution verified
✅ GitHub API integration tested
✅ Comments successfully posted to PR #5
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| GITHUB_TOKEN | Yes | GitHub Personal Access Token |
| OPENAI_API_KEY | Yes | MiniMax API Key |
| OPENAI_BASE_URL | Yes | API endpoint (https://api.minimaxi.com/v1) |
| API_HOST | No | Server host (default: 0.0.0.0) |
| API_PORT | No | Server port (default: 8000) |

## Known Limitations

1. **Webhook Signature Verification**: Commented out for local testing (enable before production)
2. **Single Repository**: Currently configured for one repository
3. **No Database**: Review history not persisted
4. **LLM-dependent**: Analysis quality depends on MiniMax model
5. **Synchronous Processing**: No message queue for handling burst traffic

## Future Roadmap

See [PHASE3_ROADMAP.md](PHASE3_ROADMAP.md) for detailed implementation plan.

### Phase 3: Enhanced Features

| Priority | Feature | Workload |
|----------|---------|----------|
| ⭐⭐⭐⭐⭐ 5/5 | Webhook Signature Verification | 2 hours |
| ⭐⭐⭐⭐☆ 4/5 | Database Storage | 6 days |
| ⭐⭐⭐☆☆ 3/5 | Markdown Reports | 3 days |
| ⭐⭐⭐☆☆ 3/5 | Multi-Repository Support | 3 days |
| ⭐⭐⭐☆☆ 3/5 | C++ Static Analysis | 8 days |
| ⭐⭐☆☆☆ 2/5 | Message Queue (Redis) | 6 days |
| ⭐⭐☆☆☆ 2/5 | GitHub App | 7 days |

## Deployment

### Local Development
```bash
python3.11 -m uvicorn src.main:app --reload --port 8000
```

### Production
```bash
# Use gunicorn for production
gunicorn src.main:app --workers 4 --bind 0.0.0.0:8000
```

### Docker (TODO)
```bash
docker build -t code-review-agent .
docker run -p 8000:8000 --env-file .env code-review-agent
```
