# ScanSci PDF

[![PyPI version](https://img.shields.io/pypi/v/scansci-pdf)](https://pypi.org/project/scansci-pdf/)
[![Python](https://img.shields.io/pypi/pyversions/scansci-pdf)](https://pypi.org/project/scansci-pdf/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-green)](https://modelcontextprotocol.io)

> 学术论文下载 MCP 服务器 — 13+ 数据源、100+ 高校 WebVPN、并行竞速下载引擎

---

## 功能特性

- **13+ 下载源** — arXiv、Sci-Hub、LibGen、Unpaywall、OpenAlex、Semantic Scholar、DOAJ、EuropePMC、CORE、PMC、出版商直链等
- **100+ 高校 WebVPN** — 中国高校机构代理访问论文全文
- **并行竞速引擎** — 多数据源同时尝试，最快可用源获胜
- **智能列表解析** — APA 引文、BibTeX、DOI 列表，自动补全缺失 DOI
- **自动重命名** — PDF 自动重命名为 `作者年份_标题.pdf` 格式
- **引文导出** — BibTeX、RIS、EndNote 格式
- **Zotero 集成** — 下载后直接推送到 Zotero
- **Tor 支持** — 通过内嵌 Tor 匿名访问 Sci-Hub/LibGen
- **网络诊断** — 自动检测 DNS 封锁、代理问题、连接故障并给出修复建议

---

## 快速开始

### 安装

```bash
pip install scansci-pdf
```

### MCP 配置

在 Claude Desktop / Claude Code 中添加：

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

<details>
<summary>HTTP 模式</summary>

```bash
scansci-pdf run --mode streamable_http --host 0.0.0.0 --port 8000
```
</details>

<details>
<summary>Docker 部署</summary>

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
</details>

### 检查环境

```bash
scansci-pdf check
```

---

## MCP 工具

### 论文下载

| 工具 | 描述 |
|------|------|
| `scansci_pdf_download` | 下载单篇论文（DOI 或 arXiv ID） |
| `scansci_pdf_batch_download` | 批量下载多篇论文 |
| `scansci_pdf_resolve_and_download` | 解析列表 → 补全 DOI → 批量下载 |

### 搜索与解析

| 工具 | 描述 |
|------|------|
| `scansci_pdf_search` | 按关键词搜索论文（OpenAlex） |
| `scansci_pdf_parse_list` | 解析 APA/BibTeX/DOI 列表文件 |

### 引文管理

| 工具 | 描述 |
|------|------|
| `scansci_pdf_citation` | 获取论文引文（BibTeX/RIS/EndNote） |
| `scansci_pdf_import_bib` | 导入 .bib 文件并下载全部论文 |
| `scansci_pdf_zotero_push` | 推送论文到 Zotero |

### WebVPN

| 工具 | 描述 |
|------|------|
| `scansci_pdf_vpnsci_login` | 浏览器 CAS 认证登录 |
| `scansci_pdf_vpnsci_test` | 测试 WebVPN 连接性 |
| `scansci_pdf_vpnsci_status` | 检查登录状态 |
| `scansci_pdf_vpnsci_schools` | 搜索支持的大学 |
| `scansci_pdf_vpnsci_set_school` | 设置当前大学 |

### 系统管理

| 工具 | 描述 |
|------|------|
| `scansci_pdf_health_check` | 检查所有数据源可用性 |
| `scansci_pdf_setup_check` | 检测系统环境并给出安装建议 |
| `scansci_pdf_config_get` / `config_set` | 查看/修改配置 |
| `scansci_pdf_cache_clear` | 清除下载缓存 |
| `scansci_pdf_network_diagnose` | 网络诊断（DNS、代理、Tor、FlareSolverr） |

### Tor 管理

| 工具 | 描述 |
|------|------|
| `scansci_pdf_tor_install` | 自动下载安装 Tor Expert Bundle |
| `scansci_pdf_tor_start` | 启动内嵌 Tor SOCKS5 代理 |
| `scansci_pdf_tor_stop` | 停止 Tor 代理 |

---

## 下载策略

| 策略 | 描述 |
|------|------|
| `fastest`（默认） | 多数据源并行，最快获胜 |
| `oa_first` | 优先开放获取，Sci-Hub 兜底 |
| `scihub_only` | 仅使用 Sci-Hub |
| `legal_only` | 仅使用合法数据源（不含 Sci-Hub/LibGen） |

---

## WebVPN 设置

通过中国高校机构代理访问论文全文：

```
1. scansci_pdf_config_set(key="vpnsci_enabled", value="true")
2. scansci_pdf_vpnsci_set_school(school="清华大学")
3. scansci_pdf_vpnsci_login  →  浏览器打开 CAS 认证
4. scansci_pdf_vpnsci_test   →  确认连接正常
5. scansci_pdf_download(identifier="...", use_vpnsci=true)
```

支持 100+ 所高校，使用 `scansci_pdf_vpnsci_schools` 搜索。

---

## 配置参考

通过 `scansci_pdf_config_set` 修改：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `scihub_enabled` | `true` | 启用 Sci-Hub |
| `download_strategy` | `fastest` | 下载策略 |
| `output_dir` | `~/.scansci-pdf/papers` | PDF 输出目录 |
| `auto_rename` | `true` | 自动重命名 PDF |
| `network_proxy` | （空） | HTTP/SOCKS 代理地址 |
| `batch_workers` | `10` | 批量下载并发数 |
| `vpnsci_enabled` | `false` | 启用 WebVPN |
| `use_tor_for_scihub` | `false` | Sci-Hub 使用 Tor |

---

## Docker 部署

```bash
docker compose up -d
```

| 服务 | 说明 | 端口 |
|------|------|------|
| `scansci-pdf` | MCP 服务器 | 8000 |
| `tor` | Tor SOCKS5 代理 | 1080 |

数据持久化在 Docker 卷 `scansci-pdf-data` 中。

---

## Tor 设置

Tor 用于在 Sci-Hub/LibGen 被封锁的地区匿名访问。

```bash
# 自动安装 Tor（约 30MB）
scansci_pdf_tor_install

# 启动 Tor 代理
scansci_pdf_tor_start

# 受限网络（防火墙封锁 Tor）使用 obfs4 桥接
scansci_pdf_tor_start(use_bridges=true)
```

二进制文件存储在 `~/.scansci-pdf/tor/`，不污染系统环境。

---

## 故障排查

**Sci-Hub 下载失败** — 运行 `scansci_pdf_health_check(detailed=true)` 查看数据源状态，域名轮换自动处理。

**Tor 连接失败** — 确认 Tor 运行在 `socks5h://127.0.0.1:1080`。Docker 部署时 Tor 自动启动。

**WebVPN 登录失败** — 需要 Chrome/ChromeDriver。登录在你的浏览器中完成，密码不经过本工具。

**下载速度慢** — 运行 `scansci_pdf_health_check(detailed=true)` 检查数据源延迟。如 Sci-Hub 在你的网络被封锁，尝试 `legal_only` 策略。

**网络问题** — 运行 `scansci_pdf_network_diagnose` 获取全面的连接诊断报告和针对性修复建议。

---

## 架构说明

本项目采用分层架构：

| 层级 | 内容 | 许可 |
|------|------|------|
| 公开层 | 所有 `.py` 源码、配置、文档 | Apache 2.0 |
| 保护层 | `_core/*.pyx`（Cython 源码） | 专有，不公开 |
| 分发层 | `_core/*.pyd`（编译二进制） | 随 PyPI 包分发 |

从 GitHub 克隆的用户使用纯 Python 回退实现（功能相同，性能略低）。从 PyPI 安装的用户自动获得编译版本。

---

## 贡献者

<a href="https://github.com/qwlei328-maker"><img src="https://avatars.githubusercontent.com/u/257463305?v=4" width="50" height="50" alt="qwlei328-maker" title="Natasha"/></a>
<a href="https://github.com/jingqingqiu1"><img src="https://avatars.githubusercontent.com/u/87510394?v=4" width="50" height="50" alt="jingqingqiu1" title="jingqingqiu1"/></a>
<a href="https://github.com/minqifeng"><img src="https://avatars.githubusercontent.com/u/61303605?v=4" width="50" height="50" alt="minqifeng" title="minqifeng"/></a>

---

## 许可证

[Apache License 2.0](LICENSE)

例外：`src/scansci_pdf/_core/` 中的 Cython 编译扩展（`.pyd`/`.so`）为预编译二进制，仅通过 PyPI 分发。其 Cython 源码（`.pyx`）为专有代码，不包含在本仓库中。
