---
name: zotero-collection-manager
description: 按Zotero Collection增量调度原始PDF材料获取、精读笔记、知识决策与校验，支持断点续跑；不要求MinerU全文。
---

# Zotero Collection Manager

```text
Fetcher → 原始PDF核验 → Analytical Writer → 来源/链接校验
        → Knowledge决策及必要更新 → Dataview Refresh（仅需要时）→ Process Log
```

- 以父条目`zotero_key`为主键；先读日志，默认仅处理指定Collection、单篇或小批量。
- 正式MinerU全文已从普通流程删除。不得自动安装MinerU、调用转换API、补全文或重跑全库。
- 已有原PDF精读笔记时先复用，必要时定向修复。空`fulltext_path`是正常状态，不是待补任务。
- 只在PDF可读、身份正确、笔记合规、引语/页码来源通过、适用知识决策及校验通过时跳过成功条目。
- Knowledge由`research-vault-knowledge-maintainer`维护：先读当前模板，解析笔记结构，再对精确主张回到原始PDF核验。已有全文仅辅助定位。
- 集合知识整理需coverage ledger；每篇范围内论文进入真实`source_notes`与模板证据区。报告总数、PDF可用数、原文已核验数、Note-only及未解决数。
- 原PDF核验的具体主张按当前schema可记`fulltext_verified`；未回原文核验的仍记`note_supported`，不伪造引语或页码。
- 缓存、批注或全文缺失不等于PDF缺失。PDF缺失、不可读和身份冲突分别记录，可重试。
- 不修改Zotero数据库，不移动原附件。临时跳过不是永久完成；永久忽略须用户明确要求。

## 状态与日志

`COMPLETE`要求`pdf_found && pdf_readable && source_verified && note && linked && validation_passed`，以及适用Knowledge决策通过；其中`linked`指笔记到原PDF的有效入口，不要求全文双向链接。

PDF-only请求可完成PDF精读但不声称Zotero入库。其余状态为`PARTIAL_NOTE_MISSING`、`PDF_NOT_FOUND`、`PDF_UNREADABLE`、`KEY_CONFLICT`、`VALIDATION_FAILED`、用户确认的`PERMANENTLY_IGNORED`。

`FULLTEXT_DEFERRED`、`PARTIAL_FULLTEXT_MISSING`和`MINERU_FAILED`只保留为历史值；复核实际PDF/笔记/知识状态后记录新结果，不机械升级历史条目。

每篇每阶段及时追加Key、标题、时间、状态、原因和路径。报告新增成功、部分完成、失败和人工复核，不以“笔记存在”判成功。

## 调度与可移植执行

共同安装同包 `research-vault-ingest-orchestrator` 及三个专项技能。优先按用户给定集合 Key 获取分页快照；集合名称有重复时不能猜父集合。只处理指定集合，包含子集合须由用户范围支持。

辅助工具使用单篇总控的 `scripts/reading_workflow.py`；材料快照覆盖所选范围全部父条目，`summary` 将无日志、PDF缺失、已失效成功记录分别保留，不能将“此前COMPLETE”当作跳过依据。每篇按单篇总控执行，并追加 `record`；恢复时对既有来源与笔记重新校验，只补缺失阶段。

若用户同时要求集合知识整理，先维护coverage ledger，逐篇记录进入哪张知识页及证据角色；未纳入者注明理由。单纯批量精读可以逐篇记录NO_KNOWLEDGE_CHANGE，不强制把每篇变成知识节点。完成报告必须列出总数、成功、已完整复用、失败/未决及各篇原因。
