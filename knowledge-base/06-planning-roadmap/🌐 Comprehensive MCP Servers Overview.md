# MCP SERVERS OVERVIEW

**Model Context Protocol (MCP)** is an open standard for connecting AI assistants to data sources, tools, and services.
This document provides a highly detailed and advanced overview of all available MCP servers with their tools.

**Last Updated**: January 2026

---

## 📊 Table of Contents

1. [Official MCP Servers](#official-mcp-servers)
2. [GitHub MCP Server - Detailed Tools](#github-mcp-server---detailed-tools)
3. [File Systems & Storage](#file-systems--storage)
4. [Databases](#databases)
5. [Communication & Collaboration](#communication--collaboration)
6. [Search & Web](#search--web)
7. [Development Tools](#development-tools)
8. [AI & ML Services](#ai--ml-services)
9. [Finance & Crypto](#finance--crypto)
10. [Cloud Platforms](#cloud-platforms)
11. [Security & Identity](#security--identity)
12. [Automation & IoT](#automation--iot)
13. [MCP Clients & Frameworks](#mcp-clients--frameworks)
14. [Installation & Configuration](#installation--configuration)

---

## 🏆 Official MCP Servers

These are **officially maintained** MCP servers from the Model Context Protocol organization:

| Server | Category | Description | Installation |
|--------|----------|-------------|--------------|
| **Filesystem** | 📂 Storage | Local file system access with configurable permissions | `npx @modelcontextprotocol/server-filesystem` |
| **Git** | 🔄 Version Control | Git repository operations (read, search, analyze) | `uvx mcp-server-git` |
| **GitHub** | 🔄 Version Control | GitHub API for repos, PRs, issues, workflows | `docker run github-mcp-server` |
| **PostgreSQL** | 🗄️ Database | PostgreSQL with schema inspection & queries | `npx @modelcontextprotocol/server-postgres` |
| **SQLite** | 🗄️ Database | SQLite operations with analysis features | `npx @modelcontextprotocol/server-sqlite` |
| **Brave Search** | 🔍 Search | Web search via Brave Search API | `npx @modelcontextprotocol/server-brave-search` |
| **Fetch** | 🔍 Web | Web content fetching for AI consumption | `npx @modelcontextprotocol/server-fetch` |
| **Puppeteer** | 🔍 Web | Browser automation for scraping | `npx @modelcontextprotocol/server-puppeteer` |
| **Memory** | 🧠 Context | Persistent memory for AI conversations | `npx @modelcontextprotocol/server-memory` |
| **Slack** | 💬 Communication | Slack workspace integration | `npx @modelcontextprotocol/server-slack` |
| **Google Drive** | ☁️ Cloud Storage | Google Drive file management | `npx @modelcontextprotocol/server-gdrive` |
| **Google Maps** | 🗺️ Location | Maps, directions, place details | `npx @modelcontextprotocol/server-google-maps` |
| **Sentry** | 📈 Monitoring | Error tracking & performance | `npx @modelcontextprotocol/server-sentry` |
| **EverArt** | 🎨 Media | AI image generation | `npx @modelcontextprotocol/server-everart` |
| **Cloudflare** ⭐ | ⚡ Cloud | Workers, KV, R2, D1 integration | Official Cloudflare |
| **Tinybird** ⭐ | 📊 Analytics | Real-time analytics platform | Official Tinybird |
| **Neon** ⭐ | 🗄️ Database | Serverless PostgreSQL management | Official Neon |
| **Qdrant** ⭐ | 🗄️ Vector DB | Vector search & memory storage | Official Qdrant |

---

## 🐙 GitHub MCP Server - Detailed Tools

The **GitHub MCP Server** is one of the most comprehensive MCP implementations. Here are all available tools:

### Repository Management Tools

| Tool | Description | Parameters | Example Use |
|------|-------------|------------|-------------|
| `get_repository` | Get repository details | `owner`, `repo` | "Get info about microsoft/vscode" |
| `list_repositories` | List user repositories | `owner`, `type`, `sort` | "List my repositories" |
| `search_repositories` | Search GitHub repos | `query`, `per_page` | "Find React component libraries" |
| `get_file_contents` | Read file from repo | `owner`, `repo`, `path`, `ref` | "Show me the README.md" |
| `create_repository` | Create new repository | `name`, `description`, `private` | "Create a new private repo" |
| `fork_repository` | Fork a repository | `owner`, `repo` | "Fork this project" |
| `list_starred_repositories` | List starred repos | `per_page` | "Show my starred repos" |

### Branch & Commit Tools

| Tool | Description | Parameters | Example Use |
|------|-------------|------------|-------------|
| `create_branch` | Create new branch | `owner`, `repo`, `branch`, `from_branch` | "Create feature/login branch" |
| `list_branches` | List all branches | `owner`, `repo` | "Show all branches" |
| `get_commit` | Get commit details | `owner`, `repo`, `sha` | "Show commit abc123" |
| `list_commits` | List commit history | `owner`, `repo`, `sha`, `per_page` | "Show last 10 commits" |
| `push_files` | Push file changes | `owner`, `repo`, `branch`, `files`, `message` | "Update config file" |

### Issue Management Tools

| Tool | Description | Parameters | Example Use |
|------|-------------|------------|-------------|
| `create_issue` | Create new issue | `owner`, `repo`, `title`, `body`, `labels` | "Create bug report" |
| `get_issue` | Get issue details | `owner`, `repo`, `issue_number` | "Show issue #42" |
| `list_issues` | List repository issues | `owner`, `repo`, `state`, `labels` | "List open bugs" |
| `update_issue` | Update existing issue | `owner`, `repo`, `issue_number`, `title`, `body` | "Close issue #42" |
| `search_issues` | Search issues/PRs | `query`, `per_page` | "Find my assigned issues" |
| `add_issue_comment` | Add comment to issue | `owner`, `repo`, `issue_number`, `body` | "Comment on issue" |

### Pull Request Tools

| Tool | Description | Parameters | Example Use |
|------|-------------|------------|-------------|
| `create_pull_request` | Create new PR | `owner`, `repo`, `title`, `head`, `base`, `body` | "Open PR to main" |
| `get_pull_request` | Get PR details | `owner`, `repo`, `pull_number` | "Show PR #123" |
| `list_pull_requests` | List PRs | `owner`, `repo`, `state`, `head`, `base` | "List open PRs" |
| `merge_pull_request` | Merge a PR | `owner`, `repo`, `pull_number`, `merge_method` | "Merge PR #123" |
| `get_pull_request_diff` | Get PR diff | `owner`, `repo`, `pull_number` | "Show PR changes" |
| `get_pull_request_files` | List PR files | `owner`, `repo`, `pull_number` | "List changed files" |
| `create_review_comment` | Add review comment | `owner`, `repo`, `pull_number`, `body`, `path` | "Review this code" |

### Code & Search Tools

| Tool | Description | Parameters | Example Use |
|------|-------------|------------|-------------|
| `search_code` | Search code in repos | `query`, `per_page` | "Find usage of useState" |
| `get_code_owners` | Get CODEOWNERS | `owner`, `repo` | "Who owns this code?" |
| `list_code_scanning_alerts` | Security alerts | `owner`, `repo`, `state` | "Show security issues" |

### Workflow & Actions Tools

| Tool | Description | Parameters | Example Use |
|------|-------------|------------|-------------|
| `list_workflows` | List GitHub Actions | `owner`, `repo` | "Show CI workflows" |
| `get_workflow_run` | Get workflow run | `owner`, `repo`, `run_id` | "Show build #456" |
| `trigger_workflow` | Trigger workflow | `owner`, `repo`, `workflow_id`, `ref` | "Run CI pipeline" |
| `list_workflow_runs` | List workflow runs | `owner`, `repo`, `workflow_id` | "Show recent builds" |

### User & Organization Tools

| Tool | Description | Parameters | Example Use |
|------|-------------|------------|-------------|
| `get_user` | Get user profile | `username` | "Show user info" |
| `search_users` | Search users | `query`, `per_page` | "Find developers" |
| `list_organization_members` | Org members | `org` | "List team members" |
| `get_organization` | Get org details | `org` | "Show organization info" |

### Notification & Activity Tools

| Tool | Description | Parameters | Example Use |
|------|-------------|------------|-------------|
| `list_notifications` | User notifications | `all`, `participating` | "Show my notifications" |
| `mark_notification_read` | Mark as read | `thread_id` | "Dismiss notification" |
| `get_activity` | Get activity feed | `username` | "Show recent activity" |

---

## 📂 File Systems & Storage

| Server | Description | Tools | Installation |
|--------|-------------|-------|--------------|
| **Filesystem** | Secure local file access | `read_file`, `write_file`, `list_directory`, `create_directory`, `move_file`, `search_files`, `get_file_info` | `npx @modelcontextprotocol/server-filesystem /path` |
| **Google Drive** | Google Drive integration | `list_files`, `read_file`, `search_files`, `upload_file` | `npx @modelcontextprotocol/server-gdrive` |
| **AWS S3** | Amazon S3 bucket access | `list_buckets`, `list_objects`, `get_object`, `put_object`, `delete_object` | `uvx mcp-server-s3` |
| **Dropbox** | Dropbox file management | `list_folder`, `download`, `upload`, `search`, `get_metadata` | Community |
| **OneDrive** | Microsoft OneDrive | `list_items`, `download`, `upload`, `search` | Community |
| **Box** | Box cloud storage | `list_files`, `download`, `upload`, `search`, `share` | Community |
| **MinIO** | S3-compatible storage | `list_buckets`, `get_object`, `put_object` | Community |
| **SFTP** | Secure file transfer | `list`, `get`, `put`, `delete`, `mkdir` | Community |

---

## 🗄️ Databases

| Server | Description | Tools | Installation |
|--------|-------------|-------|--------------|
| **PostgreSQL** | PostgreSQL database | `query`, `list_tables`, `describe_table`, `list_schemas` | `npx @modelcontextprotocol/server-postgres` |
| **SQLite** | SQLite database | `read_query`, `write_query`, `create_table`, `list_tables`, `describe_table`, `append_insight` | `npx @modelcontextprotocol/server-sqlite` |
| **MySQL** | MySQL database | `query`, `list_databases`, `list_tables`, `describe_table` | `uvx mcp-server-mysql` |
| **MongoDB** | MongoDB NoSQL | `find`, `insert`, `update`, `delete`, `aggregate`, `list_collections` | Community |
| **Redis** | Redis key-value store | `get`, `set`, `del`, `keys`, `hget`, `hset`, `lpush`, `rpush` | Community |
| **Supabase** | Supabase platform | `query`, `insert`, `update`, `delete`, `rpc`, `storage` | Community |
| **Firebase** | Firebase Realtime DB | `get`, `set`, `push`, `update`, `remove`, `query` | Community |
| **Neon** ⭐ | Serverless Postgres | `query`, `create_branch`, `list_branches`, `get_connection_string` | Official Neon |
| **Qdrant** ⭐ | Vector database | `search`, `upsert`, `delete`, `create_collection`, `list_collections` | Official Qdrant |
| **Pinecone** | Vector database | `query`, `upsert`, `delete`, `describe_index` | Community |
| **Weaviate** | Vector search | `query`, `add`, `delete`, `get_schema` | Community |
| **Elasticsearch** | Search engine | `search`, `index`, `delete`, `get`, `bulk` | Community |
| **DuckDB** | Analytical database | `query`, `load_parquet`, `export` | Community |
| **ClickHouse** | OLAP database | `query`, `insert`, `list_tables` | Community |
| **Snowflake** | Cloud data warehouse | `query`, `list_schemas`, `list_tables` | Community |
| **BigQuery** | Google BigQuery | `query`, `list_datasets`, `list_tables`, `get_schema` | Community |

---

## 💬 Communication & Collaboration

| Server | Description | Tools | Installation |
|--------|-------------|-------|--------------|
| **Slack** | Slack workspace | `list_channels`, `post_message`, `reply_to_thread`, `add_reaction`, `get_channel_history`, `get_thread_replies`, `search_messages`, `get_users`, `get_user_profile` | `npx @modelcontextprotocol/server-slack` |
| **Discord** | Discord bot | `send_message`, `list_channels`, `list_guilds`, `get_messages`, `add_reaction` | Community |
| **Microsoft Teams** | Teams integration | `send_message`, `list_channels`, `list_teams`, `get_messages` | Community |
| **Telegram** | Telegram bot | `send_message`, `get_updates`, `send_photo`, `send_document` | Community |
| **Email (IMAP/SMTP)** | Email access | `list_folders`, `search`, `read`, `send`, `reply`, `forward` | Community |
| **Gmail** | Gmail API | `list_messages`, `get_message`, `send_message`, `search`, `list_labels` | Community |
| **Outlook** | Microsoft Outlook | `list_messages`, `send_message`, `search`, `list_folders` | Community |
| **Twilio** | SMS/Voice | `send_sms`, `make_call`, `list_messages`, `get_call_logs` | Community |
| **WhatsApp** | WhatsApp Business | `send_message`, `send_template`, `get_messages` | Community |
| **Zoom** | Zoom meetings | `create_meeting`, `list_meetings`, `get_recording` | Community |
| **Linear** | Issue tracking | `create_issue`, `update_issue`, `list_issues`, `search`, `add_comment` | Community |
| **Jira** | Atlassian Jira | `create_issue`, `update_issue`, `search`, `add_comment`, `transition` | Community |
| **Notion** | Notion workspace | `search`, `get_page`, `create_page`, `update_page`, `query_database` | Community |
| **Asana** | Project management | `create_task`, `update_task`, `list_tasks`, `add_comment` | Community |
| **Trello** | Kanban boards | `create_card`, `move_card`, `list_boards`, `list_cards` | Community |
| **Confluence** | Atlassian Confluence | `search`, `get_page`, `create_page`, `update_page` | Community |

---

## 🔍 Search & Web

| Server | Description | Tools | Installation |
|--------|-------------|-------|--------------|
| **Brave Search** | Web search | `brave_web_search`, `brave_local_search` | `npx @modelcontextprotocol/server-brave-search` |
| **Fetch** | Web fetching | `fetch` (converts to markdown) | `npx @modelcontextprotocol/server-fetch` |
| **Puppeteer** | Browser automation | `navigate`, `screenshot`, `click`, `fill`, `select`, `hover`, `evaluate` | `npx @modelcontextprotocol/server-puppeteer` |
| **Playwright** | Browser automation | `navigate`, `screenshot`, `click`, `fill`, `pdf`, `evaluate` | Community |
| **Firecrawl** | Web scraping | `scrape`, `crawl`, `map`, `search` | Community |
| **Exa** | AI-powered search | `search`, `find_similar`, `get_contents` | Community |
| **Tavily** | AI search engine | `search`, `extract`, `qna` | Community |
| **SerpAPI** | Search engine results | `search`, `images`, `news`, `shopping` | Community |
| **DuckDuckGo** | Privacy search | `search`, `news`, `images` | Community |
| **Perplexity** | AI search | `search`, `ask` | Community |
| **Bing** | Microsoft Bing | `web_search`, `image_search`, `news_search` | Community |
| **YouTube** | Video search | `search`, `get_video`, `get_transcript`, `get_channel` | Community |
| **Wikipedia** | Wikipedia access | `search`, `get_page`, `get_summary` | Community |
| **ArXiv** | Academic papers | `search`, `get_paper`, `download_pdf` | Community |
| **PubMed** | Medical research | `search`, `get_article`, `get_citations` | Community |

---

## 💻 Development Tools

| Server | Description | Tools | Installation |
|--------|-------------|-------|--------------|
| **Git** | Git operations | `git_status`, `git_diff`, `git_commit`, `git_log`, `git_branch`, `git_checkout`, `git_show` | `uvx mcp-server-git` |
| **Docker** | Container management | `list_containers`, `run`, `stop`, `logs`, `exec`, `build`, `pull` | Community |
| **Kubernetes** | K8s management | `get_pods`, `get_services`, `apply`, `delete`, `logs`, `exec` | Community |
| **NPM** | Node packages | `search`, `info`, `install`, `list`, `outdated` | Community |
| **PyPI** | Python packages | `search`, `info`, `download` | Community |
| **Cargo** | Rust packages | `search`, `info`, `build`, `test` | Community |
| **VS Code** | Editor integration | `open_file`, `edit`, `search`, `run_task`, `debug` | Community |
| **JetBrains** | IDE integration | `open_file`, `refactor`, `run`, `debug` | Community |
| **Xcode** | Apple development | `build`, `test`, `run`, `archive` | Community |
| **Terraform** | Infrastructure as Code | `plan`, `apply`, `destroy`, `state`, `output` | Community |
| **Ansible** | Configuration mgmt | `playbook`, `inventory`, `vault` | Community |
| **CircleCI** | CI/CD | `list_pipelines`, `trigger`, `get_job`, `get_artifacts` | Community |
| **Jenkins** | CI/CD | `list_jobs`, `build`, `get_build`, `get_log` | Community |
| **Vercel** | Deployment | `list_projects`, `deploy`, `get_deployment`, `list_domains` | Community |
| **Netlify** | Deployment | `list_sites`, `deploy`, `get_deploy`, `list_forms` | Community |
| **Heroku** | PaaS | `list_apps`, `deploy`, `logs`, `scale`, `config` | Community |
| **Railway** | Deployment | `list_projects`, `deploy`, `logs`, `variables` | Community |
| **Render** | Cloud platform | `list_services`, `deploy`, `logs` | Community |
| **Sentry** | Error tracking | `list_issues`, `get_issue`, `resolve_issue`, `list_events` | `npx @modelcontextprotocol/server-sentry` |
| **Datadog** | Monitoring | `query_metrics`, `list_monitors`, `create_monitor`, `get_logs` | Community |
| **New Relic** | APM | `query`, `list_applications`, `get_metrics` | Community |
| **PagerDuty** | Incident mgmt | `list_incidents`, `create_incident`, `acknowledge`, `resolve` | Community |
| **Grafana** | Dashboards | `query`, `list_dashboards`, `get_dashboard` | Community |
| **Prometheus** | Metrics | `query`, `query_range`, `list_targets` | Community |

---

## 🤖 AI & ML Services

| Server | Description | Tools | Installation |
|--------|-------------|-------|--------------|
| **OpenAI** | GPT models | `chat`, `complete`, `embed`, `image_generate`, `transcribe` | Community |
| **Anthropic** | Claude models | `chat`, `complete` | Community |
| **Google AI** | Gemini models | `generate`, `embed`, `chat` | Community |
| **Hugging Face** | ML models | `inference`, `list_models`, `get_model`, `spaces` | Community |
| **Replicate** | ML inference | `run`, `list_models`, `get_prediction` | Community |
| **Stability AI** | Image generation | `generate`, `upscale`, `edit` | Community |
| **Midjourney** | Image generation | `imagine`, `upscale`, `variations` | Community |
| **ElevenLabs** | Voice synthesis | `text_to_speech`, `list_voices`, `clone_voice` | Community |
| **Whisper** | Speech-to-text | `transcribe`, `translate` | Community |
| **LangChain** | LLM framework | `chain`, `agent`, `memory`, `retrieval` | Community |
| **LlamaIndex** | Data framework | `query`, `index`, `retrieve` | Community |
| **Ollama** | Local LLMs | `generate`, `chat`, `list_models`, `pull` | Community |
| **LM Studio** | Local LLMs | `chat`, `complete`, `list_models` | Community |
| **EverArt** | AI art | `generate`, `list_models` | `npx @modelcontextprotocol/server-everart` |

---

## 💹 Finance & Crypto

| Server | Description | Tools | Installation |
|--------|-------------|-------|--------------|
| **Stripe** | Payments | `list_customers`, `create_payment`, `list_invoices`, `refund` | Community |
| **PayPal** | Payments | `create_order`, `capture`, `refund`, `list_transactions` | Community |
| **Plaid** | Banking | `get_accounts`, `get_transactions`, `get_balance` | Community |
| **Coinbase** | Crypto exchange | `get_accounts`, `get_prices`, `buy`, `sell`, `send` | Community |
| **Binance** | Crypto exchange | `get_account`, `get_ticker`, `create_order`, `get_trades` | Community |
| **CoinGecko** | Crypto data | `get_price`, `get_markets`, `get_coin`, `get_trending` | Community |
| **Alpha Vantage** | Stock data | `get_quote`, `get_time_series`, `get_fundamentals` | Community |
| **Yahoo Finance** | Financial data | `get_quote`, `get_history`, `get_news`, `get_options` | Community |
| **Bloomberg** | Financial data | `get_quote`, `get_news`, `get_analysis` | Community |
| **QuickBooks** | Accounting | `list_invoices`, `create_invoice`, `list_customers`, `get_reports` | Community |
| **Xero** | Accounting | `list_invoices`, `create_invoice`, `list_contacts`, `get_reports` | Community |

---

## ⚡ Cloud Platforms

| Server | Description | Tools | Installation |
|--------|-------------|-------|--------------|
| **AWS** | Amazon Web Services | `ec2`, `s3`, `lambda`, `dynamodb`, `sqs`, `sns`, `cloudwatch` | Community |
| **Azure** | Microsoft Azure | `vm`, `storage`, `functions`, `cosmos`, `keyvault` | Community |
| **GCP** | Google Cloud | `compute`, `storage`, `functions`, `bigquery`, `pubsub` | Community |
| **Cloudflare** ⭐ | Edge platform | `workers`, `kv`, `r2`, `d1`, `pages`, `dns`, `analytics` | Official Cloudflare |
| **DigitalOcean** | Cloud hosting | `droplets`, `databases`, `spaces`, `apps` | Community |
| **Linode** | Cloud hosting | `instances`, `volumes`, `nodebalancers` | Community |
| **Vultr** | Cloud hosting | `instances`, `block_storage`, `dns` | Community |
| **Hetzner** | Cloud hosting | `servers`, `volumes`, `networks`, `firewalls` | Community |
| **Oracle Cloud** | Oracle OCI | `compute`, `storage`, `database`, `networking` | Community |
| **IBM Cloud** | IBM services | `watson`, `cloudant`, `functions` | Community |

---

## 🔒 Security & Identity

| Server | Description | Tools | Installation |
|--------|-------------|-------|--------------|
| **Auth0** | Identity | `list_users`, `create_user`, `get_user`, `update_user`, `list_roles` | Community |
| **Okta** | Identity | `list_users`, `create_user`, `list_groups`, `assign_role` | Community |
| **1Password** | Password manager | `get_item`, `list_items`, `create_item`, `list_vaults` | Community |
| **HashiCorp Vault** | Secrets | `read`, `write`, `list`, `delete`, `seal`, `unseal` | Community |
| **AWS Secrets Manager** | Secrets | `get_secret`, `create_secret`, `update_secret`, `list_secrets` | Community |
| **Snyk** | Security scanning | `test`, `monitor`, `list_issues`, `get_project` | Community |
| **SonarQube** | Code quality | `analyze`, `get_issues`, `get_metrics`, `list_projects` | Community |
| **Trivy** | Vulnerability scan | `scan_image`, `scan_filesystem`, `scan_repo` | Community |
| **OWASP ZAP** | Security testing | `spider`, `active_scan`, `get_alerts` | Community |

---

## 🔌 Automation & IoT

| Server | Description | Tools | Installation |
|--------|-------------|-------|--------------|
| **Home Assistant** | Smart home | `list_entities`, `get_state`, `call_service`, `turn_on`, `turn_off` | Community |
| **IFTTT** | Automation | `trigger`, `list_applets` | Community |
| **Zapier** | Workflow automation | `trigger`, `list_zaps`, `get_zap` | Community |
| **n8n** | Workflow automation | `execute`, `list_workflows`, `get_execution` | Community |
| **Make (Integromat)** | Automation | `run_scenario`, `list_scenarios` | Community |
| **Raspberry Pi** | IoT | `gpio_read`, `gpio_write`, `i2c`, `spi` | Community |
| **Arduino** | IoT | `digital_read`, `digital_write`, `analog_read`, `serial` | Community |
| **MQTT** | IoT messaging | `publish`, `subscribe`, `list_topics` | Community |
| **Philips Hue** | Smart lighting | `list_lights`, `set_state`, `set_color`, `set_brightness` | Community |
| **Spotify** | Music streaming | `play`, `pause`, `next`, `search`, `get_playlist`, `add_to_queue` | Community |
| **Apple Music** | Music streaming | `play`, `search`, `get_library` | Community |
| **Sonos** | Audio | `play`, `pause`, `volume`, `group` | Community |

---

## 🖥️ MCP Clients & Frameworks

These are applications and frameworks that can **consume** MCP servers:

| Client | Type | Description | MCP Support |
|--------|------|-------------|-------------|
| **Claude Desktop** | Desktop App | Anthropic's Claude desktop application | Native MCP |
| **Claude.ai** | Web App | Claude web interface | Native MCP |
| **Cursor** | IDE | AI-powered code editor | Native MCP |
| **Windsurf** | IDE | Codeium's AI IDE | Native MCP |
| **VS Code + Copilot** | IDE Extension | GitHub Copilot with MCP | Native MCP |
| **JetBrains + Copilot** | IDE Plugin | GitHub Copilot for JetBrains | Native MCP |
| **Xcode + Copilot** | IDE Extension | GitHub Copilot for Xcode | Native MCP |
| **Eclipse + Copilot** | IDE Plugin | GitHub Copilot for Eclipse | Native MCP |
| **Visual Studio + Copilot** | IDE Extension | GitHub Copilot for VS | Native MCP |
| **Gemini CLI** | CLI | Google's Gemini command-line | Native MCP |
| **Continue** | IDE Extension | Open-source AI assistant | Native MCP |
| **Cline** | VS Code Extension | Autonomous coding agent | Native MCP |
| **Zed** | Editor | High-performance editor | Native MCP |
| **Sourcegraph Cody** | IDE Extension | AI coding assistant | Native MCP |
| **Amazon Q** | IDE Extension | AWS AI assistant | Native MCP |
| **Tabnine** | IDE Extension | AI code completion | Native MCP |
| **Codeium** | IDE Extension | Free AI coding | Native MCP |
| **LangChain** | Framework | LLM application framework | MCP Integration |
| **LlamaIndex** | Framework | Data framework for LLMs | MCP Integration |
| **Semantic Kernel** | Framework | Microsoft AI orchestration | MCP Integration |
| **AutoGen** | Framework | Multi-agent framework | MCP Integration |
| **CrewAI** | Framework | AI agent framework | MCP Integration |

---

## ⚙️ Installation & Configuration

### Quick Installation Methods

```bash
# NPM-based servers
npx @modelcontextprotocol/server-<name>

# Python-based servers (using uvx)
uvx mcp-server-<name>

# Docker-based servers
docker run -i --rm <image-name>
```

### Configuration File Locations

| Client | Config Location | Format |
|--------|-----------------|--------|
| **Claude Desktop** | `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) | JSON |
| **Claude Desktop** | `%APPDATA%\Claude\claude_desktop_config.json` (Windows) | JSON |
| **VS Code** | `.vscode/mcp.json` or settings.json | JSON |
| **Cursor** | `~/.cursor/mcp.json` | JSON |
| **Gemini CLI** | `~/.gemini/mcp_config.json` | JSON |
| **Cline** | VS Code settings | JSON |

### Example Configuration

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "github-mcp-server:latest"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    },
    "postgres": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-postgres", "postgresql://user:pass@localhost/db"]
    },
    "brave-search": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Environment Variables

| Server | Required Variables |
|--------|-------------------|
| **GitHub** | `GITHUB_PERSONAL_ACCESS_TOKEN` |
| **Brave Search** | `BRAVE_API_KEY` |
| **Slack** | `SLACK_BOT_TOKEN`, `SLACK_TEAM_ID` |
| **Google Drive** | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` |
| **Sentry** | `SENTRY_AUTH_TOKEN`, `SENTRY_ORG` |
| **PostgreSQL** | Connection string as argument |
| **SQLite** | Database path as argument |

---

## 📚 Resources

| Resource | URL |
|----------|-----|
| **MCP Specification** | https://spec.modelcontextprotocol.io |
| **Official Servers** | https://github.com/modelcontextprotocol/servers |
| **Awesome MCP Servers** | https://github.com/punkpeye/awesome-mcp-servers |
| **MCP Documentation** | https://modelcontextprotocol.io |
| **GitHub MCP Server** | https://github.com/github/github-mcp-server |
| **Anthropic MCP Guide** | https://docs.anthropic.com/en/docs/agents-and-tools/mcp |

---

## 📈 Statistics

| Metric | Count |
|--------|-------|
| **Official Servers** | 15+ |
| **Community Servers** | 200+ |
| **Categories** | 30+ |
| **Total Tools** | 1000+ |
| **Supported Clients** | 20+ |

---

## 🔑 Legend

| Symbol | Meaning |
|--------|---------|
| ⭐ | Official/Partner server |
| 📂 | File/Storage related |
| 🗄️ | Database related |
| 💬 | Communication related |
| 🔍 | Search/Web related |
| 💻 | Development tools |
| 🤖 | AI/ML services |
| 💹 | Finance/Crypto |
| ⚡ | Cloud platforms |
| 🔒 | Security/Identity |
| 🔌 | Automation/IoT |

---

*This document is a comprehensive reference for MCP servers as of January 2026. The MCP ecosystem is rapidly evolving, so check the official repositories for the latest updates.*

