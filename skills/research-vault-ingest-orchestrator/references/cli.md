# CLI 与证据记录

工具位于本技能的 `scripts/reading_workflow.py`。从仓库运行时，路径为 `skills/research-vault-ingest-orchestrator/scripts/reading_workflow.py`；安装后按真实技能位置调整。下面将其简称 `TOOL`，运行命令时替换为实际脚本路径。

## 原始材料

```text
python TOOL --config config.json material --key PARENTKEY --out local/work/snapshot.json
python TOOL --config config.json material --title "论文完整标题" --out local/work/snapshot.json
python TOOL --config config.json material --collection COLLECTIONKEY --out local/work/snapshot.json
python TOOL --config config.json material --collection-name "集合名称" --out local/work/snapshot.json
```

Key 为实际8位 Zotero Key，不能照抄示例词。集合默认仅直接成员；只有任务范围包含子集合时加 `--include-subcollections`。所有选择都有分页，父条目按 Key 去重。快照保留每篇材料，并写出同目录 `materials/<父Key>.json`。多PDF候选不自动选择，缺失/不可读附件保留真实状态。

```text
python TOOL --config config.json extract --material local/work/materials/PARENTKEY.json --pdf-key PDFKEY --pages 4,5 --out local/work/evidence/PARENTKEY
```

`extract` 输出带物理页标记的临时文本和 `pages.json`，`--pages` 为需要目视的物理页 PNG。没有 `--pages` 时只提取文本。原PDF哈希与材料快照不符则停止，先重新确认版本。文本提取结果不是正式全文档案，也不证明上下文已读。

## 笔记与 review.json

按写作技能模板建立或修复同一笔记。代理实际核验后，在工作目录建立下列证据记录；`quotes` 覆盖全部主要发现，页码必须来自PDF物理页。

```json
{
  "source_sha256": "原始PDF实际SHA256",
  "context_verified": true,
  "quotes": [
    {
      "finding_number": 1,
      "page": 6,
      "quote": "实际原文引语，不能由中文摘要反译",
      "context_verified": true
    }
  ],
  "formulas": {"applicable": true, "verified": true, "pages": [4, 5]},
  "figures": {"applicable": true, "verified": true, "pages": [9]},
  "knowledge_decision": {
    "action": "NO_KNOWLEDGE_CHANGE",
    "reason": "说明本篇尚未形成需要维护的跨论文主张"
  }
}
```

无需公式/图表时显式写 `{"applicable": false}`；存在复杂公式或图表却未核验时不能写不适用。记录 `verified: true` 必须是实际阅读/目视结果，不能由材料提取自动填入。扫描PDF需要可核验的文字/图像材料；CLI不提供OCR，不把空文本判成已核验。

Zotero笔记的发现与引语格式：

```markdown
- **主要发现 1**：中文理解，保留条件和局限。
- **原文引用 1**：[PDF第6页](zotero://open-pdf/library/items/PDFKEY?page=6)。

> 实际原文引语
```

PDF-only笔记不含伪造Key，用真实本地PDF链接，并在每条引语旁写 `PDF第6页`。父条目作者字段为空时可从PDF确认，不修改Zotero或凭空补作者。

```text
python TOOL --config config.json validate --note "实际Vault内的笔记.md" --review local/work/review.json --material local/work/materials/PARENTKEY.json --report local/work/validation.json
```

Zotero模式必须提供相符材料快照；PDF-only模式省略 `--material`。这组校验覆盖来源、身份、模板、精确引语与核验记录，不代替科学判断。Knowledge有修改时，`action`用`KNOWLEDGE_UPDATED`，在`validation_reports`里给出实际知识校验报告绝对路径；报告必须有 `passed: true`、非空`checks`及空`errors`。知识报告的schema/模板/逐篇覆盖/主张支持范围仍应按Maintainer完整核对，不能用空报告通过门槛。

## 追加记录与断点恢复

entry.json：

```json
{
  "zotero_key": "PARENTKEY",
  "state": "COMPLETE",
  "note_path": "实际相对Vault路径.md",
  "material_path": "实际材料文件绝对路径.json",
  "review_path": "实际核验记录绝对路径.json",
  "reason": "原PDF精读、笔记、引用与适用知识检查通过"
}
```

```text
python TOOL --config config.json record --entry local/work/entry.json
python TOOL --config config.json summary --snapshot local/work/snapshot.json --out local/work/summary.json
```

成功记录会再次校验后追加；不会覆盖历史日志、修改笔记状态或写回Zotero。失败记录使用实际状态和原因，例如 `PDF_NOT_FOUND`。只有Zotero模式用父Key日志；PDF-only结果保留独立报告，不制造Key调用record。

恢复时重新获取集合快照，再运行summary。它重新验证旧成功的原PDF、哈希、当前笔记和review文件，不能从日志状态或文件存在直接跳过。`unresolved`含无笔记、来源/身份问题及校验失败；调用代理逐篇处理这些记录。只对已核实的完整记录记`ALREADY_COMPLETE`。快照只描述当时的集合范围，最终报告应再次确认用户所选范围没有未解释遗漏。

集合Knowledge整理的coverage ledger另按Maintainer记录每篇证据角色、目标页、实际来源与未纳入原因；summary是处理状态摘要，不是跨论文知识覆盖的替代品。
