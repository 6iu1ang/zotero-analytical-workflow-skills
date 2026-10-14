---
name: zotero-data-fetcher
description: 按Zotero Item Key或明确标题获取元数据、父条目、PDF附件、批注与缓存，为直接PDF精读提供可追溯原始材料。
---

# Zotero Data Fetcher

只负责原始材料和身份，不翻译、总结、改写Zotero或执行全文转换。

## 输出与流程

1. 确认实际Zotero数据目录；使用可用connector/API或既有只读提取脚本。
2. 读取标题、作者、年份、DOI、Collection和父条目`zotero_key`。
3. 在子附件中确认PDF的`pdf_key`、真实`pdf_path`、是否存在/可读；可记录SHA-256。
4. 提取原始批注、Notes及`.zotero-ft-cache`（若有），分别记录是否存在。它们帮助定位，不替代正文证据。
5. 将元数据、PDF路径及原始材料交给`zotero-analytical-writer`，不进入MinerU归档阶段。

尽可能输出：`zotero_key`、`pdf_key`、`title`、`author`、`year`、`doi`、`collection`、`note_path`、`pdf_path`、`source_file`、`source_sha256`、`annotations`、`zotero_item`、`zotero_pdf`。`fulltext_path`仅在已有档案时提供。

## 原文证据

默认直接读取原始PDF。若已有可靠全文，可用于定向定位；引语上下文、实际页码、复杂公式和图表回PDF核对。原文档案不是精读前置条件；缓存或批注缺失不阻止有PDF的精读。

不猜Key；同名多候选/父附件关系冲突需报告。标题只供核对。不得修改Zotero数据库、移动原PDF或覆盖无关文件。用户提供的非Zotero PDF由总控的PDF-only分支处理，不制造Zotero身份。

## 通用辅助工具

同包单篇总控提供 `scripts/reading_workflow.py material`，通过本机 Zotero 只读 API 分页获取指定父条目及PDF子附件；数据根目录从配置读取。工具记录所有PDF候选，不自动挑选多版本。若本机API不可用，用环境中可用的只读connector或既有只读提取工具，不自动修改Zotero设置。缓存与批注只帮助定位。
