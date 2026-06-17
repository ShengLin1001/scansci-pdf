---
name: scansci-pdf
description: >
  Download academic papers, search literature, get citations, manage institutional proxy.
  TRIGGER: downloading papers, DOI, arXiv ID, Sci-Hub, paper search, literature review,
  citation export, WebVPN, "帮我下载论文", "搜索文献", "批量下载", "论文下载", "文献检索",
  or a list of DOIs/arXiv IDs.
  SKIP: discussing papers conceptually, non-academic PDFs.
---

# scansci-pdf — 学术论文下载

MCP 工具前缀：`scansci_pdf_`

## CLI 快捷方式（无需 MCP）

简单下载单篇论文时优先用 CLI，零 token 开销：

```
scansci-pdf get 10.1038/nature12373          # 下载论文
scansci-pdf get 10.1038/nature12373 --no-bibtex
scansci-pdf login                             # 机构登录
scansci-pdf check                             # 检查依赖
```

需要搜索、批量下载、WebVPN 配置时用 MCP 工具。

## 工具选择

| 需求 | 首选 | 备选 |
|------|------|------|
| 下载单篇（零配置） | `smart_download` | CLI: `scansci-pdf get` |
| 下载单篇（控制策略/Tor） | `download` | — |
| 批量下载 | `batch_download`（支持断点续传 `batch_id`） | — |
| 搜索关键词 | `search` | — |
| 用户只给了标题（无 DOI） | `search` 获取 DOI → `download` | — |
| .bib 文件批量导入 | `import_bib` | — |
| 论文列表文件（APA/DOI 列表） | `resolve_and_download` | — |
| 付费墙论文 | `login` → 用户 SSO → 重试 `download` | — |
| 引文导出 | `citation` | — |
| 推送到 Zotero | `zotero_push`（需先下载） | — |
| 查看源健康排名 | `source_scores` | — |
| 诊断问题 | `network_diagnose` 或 `health_check(detailed=true)` | — |
| 首次使用环境检测 | `auto_setup` | — |

## 付费墙登录流程

当 `download` 返回 `error_type="paywall"` 或 `action="login_required"` 时：

1. 调用 `login(identifier=同一DOI)` → 打开浏览器到论文页面
2. 提示用户："点击 Access through your institution → 选择你的机构 → 完成 SSO 登录 → 关闭浏览器"
3. 用户关闭浏览器后 cookies 自动保存
4. 重试 `download(identifier=同一DOI)`

关键：login 传入 DOI 打开该论文页面（非通用登录页），用户可直接看到机构登录按钮。Cookies 持久化，登录一次后同出版商所有论文自动复用。批量下载中多篇付费论文只需登录一次（同出版商共享 cookies）。

## 搜索 → 筛选 → 下载

用户说"帮我下载 2020 年后 X 领域的论文"：

1. `search(query="...", year_from=2020, limit=20, sort="cited_by_count")`
2. 展示结果给用户，让用户选择
3. `download` 或 `batch_download` 下载用户选择的论文

**关键：搜索后必须让用户确认，不要自动下载所有结果。**

## 论文列表文件

**.bib 文件** → `import_bib(bib_file="...")`：自动提取 DOI 并批量下载。

**其他列表文件**（.md/.txt，含 APA/DOI 引用）：

1. `parse_list(file_path="...")` → 查看解析结果
2. `resolve_and_download(file_path="...")` → 自动补全 DOI + 批量下载

`resolve_and_download` 内部自动通过 OpenAlex 补全缺失 DOI。

## WebVPN 手动配置（大多数情况用 login 即可）

```
config_set(key="vpnsci_enabled", value="true")
vpnsci_schools(query="北京")              → 搜索支持的大学
vpnsci_set_school(school="清华大学")
vpnsci_login              → 浏览器 CAS 认证
vpnsci_test               → 确认 session_valid=true
download(identifier="...", use_vpnsci=true)
```

CARSI：`config_set` carsi_enabled + carsi_idp_name → `carsi_login(publisher="...")`
EZProxy：`config_set` ezproxy_enabled + ezproxy_login_url → `ezproxy_login`

## Tor 匿名代理

Sci-Hub/LibGen 被封锁时：

```
tor_install                    → 安装 Tor（~30MB）
tor_start                      → 启动 SOCKS5 代理
tor_start(use_bridges=true)    → 网络受限时用桥接
tor_stop                      → 停止 Tor
```

`smart_download` 自动启用 Tor，无需手动传参。

## 故障排查

1. `network_diagnose` → 一键诊断（DNS、代理、Tor、FlareSolverr）
2. 按诊断结果修复（返回中包含具体 config_set 命令）
3. 下载失败时结果中的 `hint.guidance` 字段自动给出操作建议
4. 环境问题用 `setup_check` 获取安装建议
5. 缓存问题用 `cache_clear`（`identifier` 可选，省略清除全部）

## 边界情况

| 场景 | 处理 |
|------|------|
| 用户只给了标题 | `search(标题)` 获取 DOI → `download` |
| 论文不在 OpenAlex | 告知需提供 DOI 或 arXiv ID |
| 网络封锁 Sci-Hub | 配置代理或禁用 Sci-Hub（`config_set scihub_enabled false`） |
| 环境缺组件 | `setup_check` → 按建议引导安装 |
| 超出能力（读论文、翻译、综述） | 告知需其他工具 |

## 首次使用

1. `auto_setup` → 一键检测环境（Tor、Sci-Hub、CloakBrowser）
2. `smart_download(identifier="DOI")` → 下载论文
