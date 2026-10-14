---
name: zotero-analytical-writer
description: 直接读取原始PDF，按Vault或自带模板创建、更新中文精读笔记，保持引语、公式、页码和来源可追溯；不要求MinerU归档。
---

# Zotero Analytical Writer

## 模板与职责

每次新建或内容更新，先读Vault的`模板/论文精读模板.md`；没有时读本包`assets/论文精读模板.md`。新笔记从模板开始；更新在原路径规范化，不生成重复笔记。

正文顺序固定：`基本信息 → 一句话摘要 → 研究对象 → 研究方法（方法概述 → 方法分析） → 数据来源 → 研究结论 → 关联精读笔记 → 我的判断`。保留表格、标签、层级和frontmatter，清除占位符和多余公式/引用块；局限写入方法局限、数据局限和我的判断。无确认关联时保留关联节并说明。

输入为`metadata + annotations + 原始PDF → 中文精读笔记`。不执行MinerU转换、全文归档或环境安装。已有可靠全文可辅助搜索，不是前置条件。直接PDF精读可完成，不因无全文档案而记`FULLTEXT_DEFERRED`。

## 来源与身份

保留模板字段：`title`、`aliases`、`tags`、`created`、`source`、`author`、`year`、`theme`、`study_area`、`data_source`、`methodology`、`core_variable`、`key_finding`、`relevance`。字段概括真实材料，不复制大段摘要。

可确认时增加`type: literature-note`、`zotero_key`、`pdf_key`、`doi`、`collection`、`note_path`、`source_type`、`source_file`、`source_sha256`和Zotero条目/PDF入口。父条目Key是主键，附件Key区分PDF。

`fulltext_path`是已有档案的可选字段；没有时省略或留空，不创建伪链接。笔记完成后可记`note_status: original_pdf_verified`及`ingest_status: NOTE_COMPLETE`；总控最终校验后才记`COMPLETE`。未核验材料不能标已核验。

用户提供非Zotero PDF时保留真实路径、已核实书目信息与文件版本，不猜Key、Collection、DOI或URI。适用校验通过可称PDF精读完成，不称Zotero入库；以后确认身份则更新同一笔记。

## 阅读与引用

- 从PDF正文理解研究问题、对象、数据、步骤、变量、结果和局限；批注/缓存只作为定位帮助。
- 每条主要发现紧邻真实原文引用；在PDF核对上下文、否定、条件、假设、稳健性与作者边界。
- 定位不到原句写“未在当前材料中定位到可核验原文”，不能从中文摘要反向生成英文引语。
- 页码按实际PDF物理页核验后提供；未经核实写页码未验证，不猜印刷页与物理页换算。
- 公式、图表或乱码必要时渲染页面目视核对。只保留可靠原式，区分符号、单位和作者表述，不静默修正文献问题。
- 区分作者发现、方法局限与阅读者解释；过滤地址、基金、邮箱等排版噪音。
- 保留中文逻辑重构、研究关联与学术判断，不把政策建议写成已验证效果。

## Knowledge交接

笔记提供结构化地图，原始PDF提供一手证据。交接身份、PDF路径、已核验引语及页码、公式、条件与未核验边界；已有全文可选。

知识主张的`fulltext_verified`按当前schema表示已回原文（PDF或既有全文）核验；仅笔记支持用`note_supported`，跨论文解释用`interpretation`。不因笔记含摘要就自动提升主张。

## 写入与检查

检查YAML、模板章节、占位符、公式分隔符、发现—引语配对、真实关联笔记及原PDF入口。核对身份、PDF存在/可读、文件哈希和引语页码。已有档案链接仅在声明存在时核验，不要求补档。

不批量重写历史笔记。新建时只刷新实际存在且受影响的Dataview索引；更新时仅在标题、路径或索引字段变化时定向刷新，不创建整套架构。

## 校验交接

使用本包单篇总控辅助工具时，按其 `references/cli.md` 创建review.json：真实PDF哈希、每条发现的原文引语和物理页码、实际阅读上下文/公式/图表核验记录。不能让提取脚本或“笔记已写”自动填写人工核验为通过。验证失败应修正笔记或标记未核验；原文表格/符号内部矛盾应保留并分析，不静默修正文献。
