---
name: cthulhu-note
description: 讀取、新增、刪除、修改使用者的 cthulhu-note GTD 子彈筆記清單（bujo.csv）
user-invocable: true
metadata: {"openclaw":{"emoji":"🦑","requires":{"bins":["cthulhu-note","python3"]}}}
---

# cthulhu-note skill

你可以幫使用者管理他們的個人 GTD 子彈筆記系統 **cthulhu-note**。
資料儲存在本機 CSV 檔，透過以下指令直接讀寫。

---

## 資料位置

- **CSV 檔**：`~/.local/share/cthulhu-note/bujo.csv`
- **設定檔**：`~/.config/cthulhu-note/config.toml`

---

## 資料結構

每一筆項目（item）有以下欄位：

| 欄位 | 說明 |
|------|------|
| `id` | 唯一數字 ID |
| `content` | 項目文字內容 |
| `level` | 層級：0=收件匣、1=進行中、2=子任務、3=長期參考 |
| `parent_tag` | 父層 tag（Lv2 子任務用），空字串表示無 |
| `pinned` | 是否釘選為「代辦三格」（true/false），最多 3 個 |
| `created_at` | 建立時間（ISO 8601） |
| `memos_id` | 推送到 Memos 後的 ID，空字串表示未推送 |

**層級說明：**
- **Lv0 收件匣**：剛捕捉的想法，尚未處理
- **Lv1 進行中**：今天或近期要做的事（上限 10 個）
- **Lv2 子任務**：屬於某個 Lv1 項目的細項，content 格式為 `[tag]內容`
- **Lv3 長期參考**：備忘、知識、長期目標

---

## 操作指令

### 查看所有項目
```bash
cthulhu-note --json list
```
回傳 JSON 陣列，包含全部 items。

### 查看代辦三格（今天重點）
```bash
cthulhu-note today
```
顯示目前釘選的 Lv1 項目（最多 3 個）。

### 新增項目（預設進入 Lv0 收件匣）
```bash
cthulhu-note add "項目內容"
```

### 刪除項目
```bash
python3 -c "from cthulhu_note.skill import bujo_delete; print(bujo_delete(ID))"
```
把 `ID` 換成要刪除的數字 id。

### 修改項目
```bash
python3 -c "from cthulhu_note.skill import bujo_update; print(bujo_update(ID, content='新內容', level=1, pinned=True))"
```
所有參數（content、level、pinned、parent_tag）都是選填，不填就保留原值。

### 直接查詢（過濾特定 level）
```bash
python3 -c "from cthulhu_note.skill import bujo_list; print(bujo_list(level=1))"
```

---

## 對話模式

使用者說的話 → 你要做的動作：

| 使用者說 | 動作 |
|----------|------|
| 「幫我記一下 X」、「加 X」、「記 X」 | `cthulhu-note add "X"` |
| 「今天要做什麼」、「代辦」、「三格」 | `cthulhu-note today` |
| 「全部清單」、「有什麼待辦」 | `cthulhu-note --json list` 然後整理回覆 |
| 「刪掉 X」、「X 完成了」、「刪 #ID」 | 先 list 找到 id，再 `bujo_delete(id)` |
| 「改 X 的內容」、「把 X 改成 Y」 | 先 list 找到 id，再 `bujo_update(id, content="Y")` |
| 「X 升到進行中」、「X 變 Lv1」 | `bujo_update(id, level=1)` |
| 「釘選 X」、「X 加入代辦三格」 | `bujo_update(id, pinned=True)` |
| 「X 不急了」、「X 取消釘選」 | `bujo_update(id, pinned=False)` |

---

## 回覆風格

- 一律用**繁體中文**回覆
- 操作成功後，用一句話確認：「好，已幫你加入『X』到收件匣」
- 列出清單時，依 level 分組顯示，釘選項目加 📌
- 如果 Lv1 已達 10 個，提醒使用者「進行中已滿，建議先處理一些」
- 如果代辦三格已達 3 個，提醒「代辦三格已滿，無法再釘選」

---

## 範例對話

**使用者**：幫我記一下要買牛奶
**你**：
```bash
cthulhu-note add "買牛奶"
```
好，已幫你把「買牛奶」加進收件匣 Lv0。

---

**使用者**：今天要做什麼
**你**：
```bash
cthulhu-note today
```
（解讀輸出後）你今天的代辦三格是：
📌 寫報告
📌 打電話給媽媽

---

**使用者**：寫報告完成了
**你**：
```bash
cthulhu-note --json list
```
（找到「寫報告」的 id，例如 id=3）
```bash
python3 -c "from cthulhu_note.skill import bujo_delete; print(bujo_delete(3))"
```
好，「寫報告」已完成並移除，做得好！
