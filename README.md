# Zotero 单篇与批量精读 Skills

将 Zotero 原始 PDF 精读成中文 Obsidian 笔记，并用来源、引语、页码、公式及逐篇状态记录保证可追溯性。包含单篇入口、集合批量入口和三个专项技能，可增量处理与断点续跑。

```text
指定论文 / 指定集合
→ 检查已有笔记及真实状态
→ Zotero 父条目、元数据、原始 PDF
→ 原文阅读及引语 / 图表 / 公式核验
→ 按模板写中文精读笔记
→ 来源、模板与引用校验
→ Knowledge 更新或 NO_KNOWLEDGE_CHANGE
→ 适用校验及追加日志
```

普通精读不包含正式 MinerU 全文转换或归档。已有全文可以辅助定位，PDF 原文始终是一手证据；没有全文 Markdown 不构成失败。

## 包含哪些技能

| 技能 | 作用 |
| --- | --- |
| `research-vault-ingest-orchestrator` | 单篇精读总控，支持指定 Zotero 论文或 PDF-only 模式 |
| `zotero-collection-manager` | 集合批量调度、覆盖清单、增量复用与失败重试 |
| `zotero-data-fetcher` | 只读确认身份、PDF 附件、元数据和批注 |
| `zotero-analytical-writer` | 按模板形成中文理解、方法分析、发现与原文引语 |
| `research-vault-knowledge-maintainer` | 从笔记回原始 PDF，维护有证据支持的跨论文知识 |

这五个技能组成一套工作流，建议一起安装。论文模板在写作技能的 `assets/`，知识模板和冻结 schema 在知识维护技能中；安装后无需依赖仓库顶层模板目录。

## 安装

把 `skills/` 内五个同名目录放入 Codex 技能目录（通常为用户目录下的 `.codex/skills/`）。若已经安装同名技能，先备份，再按需要更新；不要把仓库根目录当成一个技能。已有配置、Vault 与 Zotero 数据保持各自位置。

也可以在 Codex 中请求从本仓库的五个 `skills/<技能名>` 路径安装。重新开启会话后，按技能名显式调用或用普通语言指定精读任务。

## 使用示例

单篇：

```text
用 $research-vault-ingest-orchestrator 精读 Zotero 中的《论文完整标题》，
将笔记保存到我指定的 Obsidian Vault，核对关键结论、方法、公式及原文页码。
```

批量：

```text
用 $zotero-collection-manager 精读 Zotero 的“集合名称”。
只处理该集合，复用已核验的完整笔记，逐篇报告成功、失败和未解决问题。
```

仅有本地 PDF 时可以直接精读，保留实际路径和已确认书目信息，不制造 Zotero Key。存在同名条目、多个 PDF 版本或同名集合时，通过真实 Key 解决歧义。

## 可选辅助工具

辅助工具负责确定性操作，代理仍需实际阅读 PDF、判断引用上下文、目视公式和图表，并撰写科学分析。脚本不会自动把缓存内容变成精读，也不会仅凭笔记存在判定完成。

需要 Python 3.10+。安装 `requirements.txt` 中的依赖后，将 `config.example.json` 复制为本地 `config.json`，设置真实路径：

| 配置 | 含义 |
| --- | --- |
| `vault_root` | 已存在的 Obsidian 文献笔记库 |
| `zotero_data_dir` | Zotero 数据目录，内部包含 `storage/` |
| `zotero_api_base` | 开启的本机只读 API，默认 `http://127.0.0.1:23119/api/users/0` |
| `work_dir` | 临时材料和校验报告目录 |
| `process_log` | 只追加的逐篇处理日志 |

相对路径以配置文件所在目录为基准。本机 API 不可用时，可由代理使用已有只读连接工具；辅助 CLI 仅支持本机 API。Linked-file 附件若依赖 Zotero 相对附件基目录，需要另行确认实际路径。

CLI 命令及证据记录见 [使用说明](skills/research-vault-ingest-orchestrator/references/cli.md)。批量时先保存集合分页快照，每篇再走完整单篇流程；`summary` 会重新检查旧成功记录对应的来源与笔记，原 PDF 丢失或变更不会被跳过。

## 完成与证据边界

- 父条目与附件身份、PDF 路径/可读性/哈希、模板、发现—引语配对、物理页码及实际链接必须核验。
- 代码可以核对原句是否位于指定页，不能判断否定、条件、机制或因果解释是否正确；这些由实际原文阅读确认。
- 知识主张的 `fulltext_verified` 表示回原始 PDF 或已有全文核验；`note_supported` 只表示笔记支持，`interpretation` 表示阅读者解释。页面级证据汇总使用不同字段值，详见冻结 schema。
- 原文内部矛盾保留并分析，不静默修正文献。缺失 PDF、身份冲突、引用失败与未验证公式分别记录；不将遗漏论文算作批量成功。
- `NO_KNOWLEDGE_CHANGE` 是正常成功决策。未形成耐久跨论文证据时，保留单篇笔记即可。

本仓库只发布工作流、模板与通用工具，不包含个人论文、PDF、阅读缓存、Vault 笔记或本地处理记录。

## 验证与打包

```text
python -m unittest discover -s tests -v
python scripts/check_package.py
python scripts/package.py
```

测试使用程序生成的最小 PDF，覆盖材料分页、附件身份、PDF 缺失、错误页码、哈希变更及旧成功记录失效。`check_package.py` 检查技能 frontmatter、UI 元数据、相对资源链接、模板/schema一致性与发布文件；Codex 自带 `quick_validate.py` 可再逐技能运行。打包输出五个独立 `.skill` 文件和一个完整技能包 ZIP，均位于忽略的 `dist/`。
