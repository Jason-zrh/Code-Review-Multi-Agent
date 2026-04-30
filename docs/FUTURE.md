# 未来规划

> 状态：规划中

## 功能优先级

| 优先级 | 功能 | 工作量 | 说明 |
|--------|------|--------|------|
| ⭐⭐⭐⭐⭐ | Webhook 签名验证 | 2 小时 | 安全是底线，只需启用 |
| ⭐⭐⭐⭐☆ | 数据库存储 | 6 天 | 审查历史持久化 |
| ⭐⭐⭐☆☆ | Markdown 报告 | 3 天 | 格式化审查摘要 |
| ⭐⭐⭐☆☆ | 多仓库支持 | 3 天 | 一套系统管理多仓库 |
| ⭐⭐⭐☆☆ | C++ 静态分析 | 8 天 | clang-tidy/cppcheck 集成 |
| ⭐⭐☆☆☆ | 消息队列 | 6 天 | Redis 解耦处理 |
| ⭐⭐☆☆☆ | GitHub App | 7 天 | 更好的权限控制 |

## 建议实施顺序

### 第一阶段（必须）

**Webhook 签名验证**
- 取消 `src/github/webhook.py` 中的注释
- 配置 `GITHUB_WEBHOOK_SECRET` 环境变量
- 预估：2 小时

### 第二阶段（推荐）

**数据库存储 + Markdown 报告**
- 显著提升可用性
- 预估：9 天

### 第三阶段（可选）

**多仓库支持 + C++ 静态分析**
- 特定场景需要
- 预估：11 天

### 第四阶段（高级）

**消息队列 + GitHub App**
- 大规模部署时考虑
- 预估：13 天

## 功能详情

### 1. Webhook 签名验证

启用 GitHub Webhook 的 HMAC-SHA256 签名验证，防止伪造请求。

```python
# src/github/webhook.py 中已有代码，取消注释即可
def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        settings.github_webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### 2. 数据库存储

存储审查历史，支持查询和趋势分析。

```
数据库表设计：
├── ReviewRecord     # 审查记录
│   ├── pr_id, repo, status, created_at
│   └── comments_count, critical_count
│
└── ReviewComment    # 审查评论
    ├── review_id, file, line, severity
    └── category, message
```

### 3. Markdown 报告

生成格式化的审查摘要报告。

```markdown
# Code Review Report - PR #123

## 概要
| 类型 | 数量 |
|------|------|
| 🔴 Critical | 2 |
| 🟠 High | 5 |

## 安全问题
- **文件**: payment.py:13
- **问题**: SQL 注入漏洞
- **建议**: 使用参数化查询
```

### 4. 多仓库支持

配置多个 GitHub 仓库，自动识别并应用不同规则。

```python
REPOSITORIES = [
    {"owner": "my-org", "repo": "frontend", "rules": ["security", "bug", "style"]},
    {"owner": "my-org", "repo": "backend", "rules": ["security", "bug"]},
]
```

### 5. C++ 静态分析

集成 clang-tidy 和 cppcheck，对 C++ 代码进行确定性检测。

### 6. 消息队列

使用 Redis 解耦 Webhook 接收和实际审查处理，支持多 Worker 并行。

### 7. GitHub App

从 Webhook 升级，获得更好的权限控制和事件处理，无需 ngrok。
