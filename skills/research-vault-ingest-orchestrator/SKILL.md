---
name: research-vault-ingest-orchestrator
description: 编排指定论文的原始PDF精读、笔记、Knowledge决策和校验；正式MinerU全文归档不属于入库流程。
---

# ResearchVault Ingest Orchestrator

## 当前工作流

Vault：`config.vault_root` 所指定的实际 Vault。以实际目录为准，不为满足惯例创建索引或知识库架构。

```text
指定论文 → 状态检查 → Zotero身份/原始PDF → 原文阅读与核验
        → 中文精读笔记 → 笔记/PDF来源校验 → Knowledge决策
        → 必要的Knowledge更新或NO_KNOWLEDGE_CHANGE → 最终校验 → 追加日志
```

本流程直接精读原始PDF。普通入库不安装、调用或调试MinerU，不上传PDF到转换API，不生成正式全文Markdown。PDF可读且适用校验通过即可完成，空`fulltext_path`不导致部分完成。已有全文可辅助定位，但不触发补档或重跑。

## 专项skills

1. `zotero-data-fetcher`：确认父条目`zotero_key`、附件`pdf_key`、元数据和实际PDF。
2. `zotero-analytical-writer`：按模板阅读原始PDF，创建或原位补齐单篇笔记。
3. `research-vault-knowledge-maintainer`：基于笔记结构与原始PDF决定知识更新。

Collection任务转给同包的`zotero-collection-manager`。本包不含正式全文归档工具；若用户另行明确要求归档，按其指定工具处理。

## 模式与最小动作

- `NORMAL_INGEST`：指定Zotero论文；检查状态，核对PDF，只执行缺失的笔记/知识阶段和标准校验。
- `PDF_ONLY_INGEST`：用户提供PDF、尚无确认的Zotero身份；直接阅读和写笔记，保留实际路径，不猜Zotero Key、Collection或URI。适用PDF/模板校验通过可完成PDF精读，不称为Zotero入库。以后识别身份时更新同一笔记。
- `ACCEPTANCE_TEST`：仅用户明确要求系统、检索或新主题验收时运行扩展测试。

| 已有状态 | 必要动作 |
| --- | --- |
| PDF、模板合规笔记、来源核验和知识决策均有效 | `ALREADY_COMPLETE` |
| 笔记合规且原始PDF有效，仅旧状态是全文待补 | 定向校验后追加新状态；不运行转换 |
| 笔记模板不合规 | 原路径修整模板，保留身份和已核实内容，再校验 |
| 原始PDF有效但笔记缺失 | 只执行原文阅读与笔记阶段 |
| 笔记有效但未做知识决策 | 只执行知识决策和适用校验 |
| PDF缺失/不可读、身份冲突或验证失败 | 保留真实可重试/人工复核状态；不声明完成 |

标题仅用于显示和核对，以父条目Key为稳定身份。`NO_KNOWLEDGE_CHANGE`是成功的知识决策。没有耐久贡献时不因完成一篇笔记而强行创建知识页。

## 原文与完成条件

每条发现配实际原句，检查上下文、否定、条件、局限与页码。公式和图表必要时目视核对PDF。临时文本提取和页面渲染是工作材料，不是正式全文档案；不能用缓存或中文摘要反向生成引语。

新建或更新笔记使用Vault模板，否则用`templates/论文精读模板.md`。保留原始PDF入口、身份、`source_file`、可核实的文件哈希及`note_path`；`fulltext_path`仅是已有档案的可选字段。

知识维护同时读取笔记结构与PDF原文。`fulltext_verified`按当前知识schema表示具体主张已在原文（PDF或已有全文）核验，不表示生成了MinerU档案。没有实际原文核验仍用`note_supported`；跨论文解释用`interpretation`。不自动提升旧主张证据状态。

集合/全部论文任务需逐篇coverage ledger、真实`source_notes`、模板证据区、无未解释遗漏。报告PDF可用、已核验、Note-only和未解决数量。

最终必须通过身份、PDF来源、模板、引用/页码、公式、真实链接及适用Knowledge检查。标准检查不能因取消转换而省略。若官方验证器缺失，报告本地校验及其边界，不称官方通过。只追加机器日志；已有Knowledge日志按Maintainer规则追加，不为日志惯例创建缺失架构。历史记录保留；历史部分状态仅在定向复核后更新。

细节见[流程](references/pipeline.md)、[关卡](references/ingest-gates.md)、[状态](references/workflow-states.md)、[校验](references/validation-contract.md)、[架构](references/system-architecture.md)。

## 可移植配置与工具

本包依赖共同安装的材料获取、笔记写作、知识维护技能；批量入口另装 `zotero-collection-manager`。按实际安装路径定位同包技能，不能假设本机绝对路径。缺少依赖时仍可按本节和参考流程完成已授权的原文阅读，明确缺少的专项能力。

读取用户配置的 `vault_root`、`zotero_data_dir`、`work_dir` 和 `process_log`；没有配置时从当前项目/用户指示确认真实位置，不写入示例路径。临时文本与页面渲染只放工作目录。

通用辅助工具在 [scripts/reading_workflow.py](scripts/reading_workflow.py)，用法见 [CLI与证据记录](references/cli.md)。工具能获取指定材料、提取/渲染、核对笔记与引语、汇总批量状态；不能代替阅读上下文或自动生成科学判断。程序校验与人工原文核验均通过后才声明完成。
