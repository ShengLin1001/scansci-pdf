# ScanSci PDF

> 学术论文下载 MCP 服务器 — 支持 13+ 数据源、100+ 高校 WebVPN、并行下载

`Python 3.11+` `MCP 兼容` `Docker 就绪`

---

## 功能特性

- **13+ 下载源**：arXiv、Sci-Hub、LibGen、Unpaywall、OpenAlex、Semantic Scholar、DOAJ、EuropePMC、CORE、PMC、出版商直链等
- **多校 WebVPN**：100+ 所中国高校机构代理
- **并行下载**：多数据源同时尝试，自动选择最快可用源
- **论文列表解析**：APA 引文、BibTeX、DOI 列表，自动补全缺失 DOI
- **自动重命名**：PDF 自动重命名为 `作者年份_标题.pdf` 格式
- **引文导出**：BibTeX、RIS、EndNote 格式
- **Zotero 集成**：下载后直接推送到 Zotero
- **Tor 支持**：通过 Tor 代理访问 Sci-Hub/LibGen

---

## 快速开始

### 安装

```bash
pip install scansci-pdf
```

### 启动 MCP 服务器

```bash
# stdio 模式（Claude Desktop / Claude Code）
scansci-pdf run

# HTTP 模式（Web 调用）
scansci-pdf run --mode streamable_http --host 0.0.0.0 --port 8000
```

### 检查依赖

```bash
scansci-pdf check
```

### MCP 配置

在 Claude Desktop 或 Claude Code 中添加：

```json
{
  "mcpServers": {
    "scansci-pdf": {
      "command": "scansci-pdf",
      "args": ["run"]
    }
  }
}
```

Docker 方式：

```json
{
  "mcpServers": {
    "scansci-pdf": {
      "command": "docker",
      "args": ["compose", "-f", "path/to/docker-compose.yml", "run", "--rm", "scansci-pdf"]
    }
  }
}
```

---

## MCP 工具一览

### 论文下载

| 工具 | 描述 | 关键参数 |
|------|------|----------|
| `scansci_pdf_download` | 下载单篇论文 | `identifier`（必需，DOI 或 arXiv ID）、`strategy`、`use_vpnsci`、`use_tor` |
| `scansci_pdf_batch_download` | 批量下载多篇论文 | `identifiers`（必需，列表）、`use_vpnsci`、`use_tor` |
| `scansci_pdf_resolve_and_download` | 完整流水线：解析列表 → 补全 DOI → 批量下载 | `file_path`（必需）、`resolve_titles` |

### 搜索与解析

| 工具 | 描述 | 关键参数 |
|------|------|----------|
| `scansci_pdf_search` | 按关键词搜索论文（OpenAlex） | `query`（必需）、`limit`、`year_from`、`year_to`、`sort` |
| `scansci_pdf_parse_list` | 解析 APA/BibTeX/DOI 列表文件 | `file_path`（必需） |

### 引文管理

| 工具 | 描述 | 关键参数 |
|------|------|----------|
| `scansci_pdf_citation` | 获取论文引文 | `identifier`（必需）、`format`（bibtex/ris/endnote） |
| `scansci_pdf_import_bib` | 导入 .bib 文件并下载全部论文 | `bib_file`（必需） |
| `scansci_pdf_zotero_push` | 推送论文到 Zotero | `identifier`（必需） |

### WebVPN 管理

| 工具 | 描述 | 关键参数 |
|------|------|----------|
| `scansci_pdf_vpnsci_login` | 打开浏览器进行 CAS 认证登录 | 无 |
| `scansci_pdf_vpnsci_test` | 测试 WebVPN 连接性 | `doi`（可选） |
| `scansci_pdf_vpnsci_status` | 检查 WebVPN 登录状态 | 无 |
| `scansci_pdf_vpnsci_schools` | 搜索支持的大学 | `query`（可选，如"清华"） |
| `scansci_pdf_vpnsci_set_school` | 设置当前大学 | `school`（必需，如"清华大学"） |

### 系统管理

| 工具 | 描述 | 关键参数 |
|------|------|----------|
| `scansci_pdf_health_check` | 检查所有数据源可用性 | `detailed`（默认 false） |
| `scansci_pdf_setup_check` | 检测系统环境并给出安装建议 | 无 |
| `scansci_pdf_config_get` | 查看当前配置 | 无 |
| `scansci_pdf_config_set` | 修改配置项 | `key`（必需）、`value`（必需） |
| `scansci_pdf_cache_clear` | 清除下载缓存 | `identifier`（可选，省略则清除全部） |

### Tor 管理

| 工具 | 描述 | 关键参数 |
|------|------|----------|
| `scansci_pdf_tor_install` | 自动下载安装 Tor Expert Bundle | 无 |
| `scansci_pdf_tor_start` | 启动内嵌 Tor SOCKS5 代理 | `use_bridges`（默认 false） |
| `scansci_pdf_tor_stop` | 停止内嵌 Tor 代理 | 无 |

---

## 下载策略

| 策略 | 描述 |
|------|------|
| `fastest`（默认） | 多数据源并行，自动选择最快可用源 |
| `oa_first` | 优先尝试合法开放获取源，Sci-Hub 作为兜底 |
| `scihub_only` | 仅使用 Sci-Hub |
| `legal_only` | 仅使用合法数据源（不含 Sci-Hub/LibGen） |

---

## WebVPN 设置

WebVPN 通过中国高校机构代理访问论文全文，5 步启用：

```bash
# 1. 启用 WebVPN
scansci_pdf_config_set key=vpnsci_enabled value=true

# 2. 设置你的大学
scansci_pdf_vpnsci_set_school school=清华大学

# 3. 登录（浏览器打开 CAS 认证）
scansci_pdf_vpnsci_login

# 4. 测试连接
scansci_pdf_vpnsci_test

# 5. 使用 WebVPN 下载
scansci_pdf_download identifier=10.1038/nature12373 use_vpnsci=true
```

支持 100+ 所高校，使用 `scansci_pdf_vpnsci_schools` 搜索。部分示例：

> 清华大学、北京大学、浙江大学、上海交通大学、复旦大学、南京大学、中国科学技术大学、华中科技大学、武汉大学、中山大学……

---

## 配置参考

关键配置项（通过 `scansci_pdf_config_set` 修改）：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `scihub_enabled` | `true` | 启用 Sci-Hub |
| `download_strategy` | `fastest` | 下载策略 |
| `output_dir` | `~/.scansci-pdf/papers` | PDF 输出目录 |
| `auto_rename` | `true` | 自动重命名 PDF |
| `network_proxy` | （空） | HTTP/SOCKS 代理地址 |
| `batch_workers` | `10` | 批量下载并发数 |
| `email` | （占位符） | Unpaywall API 邮箱 |
| `vpnsci_enabled` | `false` | 启用 WebVPN |
| `vpnsci_school` | `清华大学` | 默认大学 |
| `use_tor_for_scihub` | `false` | Sci-Hub 使用 Tor |

---

## Docker 部署

```bash
docker compose up -d
```

启动服务：

| 服务 | 说明 | 端口 |
|------|------|------|
| `scansci-pdf` | MCP 服务器 | 8000 |
| `tor` | Tor SOCKS5 代理 | 1080 |

数据持久化在 Docker 卷 `scansci-pdf-data` 中。

---

## 环境配置

运行 `scansci_pdf_setup_check` 可自动检测系统环境并给出安装建议。

### Tor 安装

Tor 用于匿名访问 Sci-Hub/LibGen，在网络封锁 Sci-Hub 的地区必需。

**推荐方式：内嵌 Tor（无需 Docker）**

```
# 自动下载安装 Tor Expert Bundle
scansci_pdf_tor_install

# 启动 Tor 代理
scansci_pdf_tor_start

# 受限网络（防火墙封锁 Tor）使用 obfs4 桥接
scansci_pdf_tor_start(use_bridges=true)
```

Tor 二进制自动下载到 `~/.scansci-pdf/tor/`，不污染系统环境。首次使用时下载约 30MB。

**备选方式：Docker**
```bash
docker compose up -d tor    # 启动 Tor 容器，监听 1080 端口
```

使用的镜像：[`shahradel/torproxy`](https://github.com/shahradel/TorProxy)（轻量 Tor SOCKS5 代理，仅 30MB）。

**手动安装：**

| 系统 | 命令 |
|------|------|
| Windows | 下载 [Tor Expert Bundle](https://www.torproject.org/download/tor/)，解压后运行 `tor.exe` |
| macOS | `brew install tor && brew services start tor` |
| Ubuntu/Debian | `sudo apt install tor && sudo systemctl enable --now tor` |

默认端口：`1080`（Docker）/ `9050`（手动安装）。可通过 `scansci_pdf_config_set key=network_proxy value=socks5h://127.0.0.1:9050` 修改。

### Docker 安装

| 系统 | 方式 |
|------|------|
| Windows | [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)（需 WSL2） |
| macOS | [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)（支持 Apple Silicon） |
| Linux | `curl -fsSL https://get.docker.com \| sh` |

---

## 常见问题

**Sci-Hub 下载失败**
Sci-Hub 域名经常变化，工具会自动处理。运行 `scansci_pdf_health_check detailed=true` 查看各数据源状态。

**Tor 连接不上**
确保 Tor 运行在 `socks5h://127.0.0.1:1080`。Docker 部署时 Tor 自动启动。

**WebVPN 登录失败**
WebVPN 需要 Chrome/ChromeDriver。登录在你的浏览器中完成，密码不会经过本工具。

**下载速度慢**
运行 `scansci_pdf_health_check detailed=true` 检查各数据源延迟。如果 Sci-Hub 在你的网络中被封锁，尝试 `legal_only` 策略。

---

## 许可证

专有许可证 - 保留所有权利。详见 [LICENSE](LICENSE)。
