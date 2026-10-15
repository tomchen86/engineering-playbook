# engineering-playbook

一個人加上 AI agent 開發軟體時的工作方法，加上一個可以直接複製的初始 repo。不綁定程式語言。

| 路徑 | 內容 |
|---|---|
| [`PLAYBOOK.md`](PLAYBOOK.md) | 這套系統的需求：每個做法要保證什麼、為什麼、什麼時候改（第 0～7 章）。修改系統或第一次採用時讀，日常開發不用讀 |
| [`starter/`](starter/) | 示範性的初始 repo，開新專案時整包複製 |
| [`tests/`](tests/) | `trace_check.py`、`spec-check.sh` 和 starter 設定的自我測試 |

## 平常你只做兩件事

決定要做什麼（開 Issue、排 roadmap）之後，每個會改變行為的功能，你只要做兩個決定：

1. **認可 spec**：規格作者開好 draft PR 後，看裡面 spec 的 diff，說「可以」。
2. **同意合併**：看完審查者的回報，說「可以合併」。

不改變行為的 PR（錯字、文件、重構、套件更新）只有第 2 件。其餘的 Git 操作，包括建立 `spec/` 分支、同步、比對和合併後清理，都由 agent 照 `skills/` 執行。有標 `(manual)` 的 requirement 時，發版前還要照清單在實機上驗收（第 1 章）。

## 開新專案

1. 複製 starter，建立 git repo：
   ```bash
   cp -R starter ../my-app && cd ../my-app && git init -b main
   ```
2. 第 0 章：確認這是會長期維護的產品（starter 照這個等級設計），填好 `docs/adr/0001-follow-engineering-playbook.md`，並記下這份 playbook 的 commit。
3. 選技術：填好 `scripts/check.sh`（測試結果輸出成 JUnit XML 到 `reports/junit/`），並在 `.github/workflows/ci.yml` 加上工具鏈的 setup 步驟。
4. 填好 `README.md` 和 `AGENTS.md` 裡的專案說明和指令。驗收測試預設放在 `tests/acceptance/`，已附 `.gitkeep`；只有測試工具找不到那裡時（例如 monorepo 裡每個 app 各有自己的測試設定），才改 `AGENTS.md` 的 Acceptance tests 那一行。把 `skills/` symlink 到你用的 agent 工具讀 skill 的位置（第 1 章）。review 的 spec 檢查需要 Git 2.43 以上。
5. 建立 GitHub repo 並 push，執行 `bash scripts/setup-github.sh`。
6. 寫好 `docs/roadmap.md` 的目標和 Not doing；把實作者的 bot 帳號加成 collaborator，再做完第 3 章的驗證。需要時再建 GitHub Project（第 1、3 章）。
7. 第一個功能開始時，照第 1 章的流程寫第一份 spec。

也可以把 `starter/` 推成一個獨立的 repo，在 GitHub 上設成 template repository，之後用 `gh repo create my-app --template <owner>/<repo> --clone` 開新專案。starter 的 CI 在 template repository 本身不會執行。

## 修改這份 playbook

- 改到某個保證或決定（要成立什麼、為什麼）時，同一個 commit 要更新 `PLAYBOOK.md` 對應的章節。只改指令或步驟的寫法時，只動 skills 或腳本，不用動 PLAYBOOK。
- 自我測試：`python3 -m unittest discover -s tests -v`，CI 也會跑。
- 已經複製出去的專案不會自動更新。等有兩個以上的專案、同一個檔案已經改過兩次，再把 CI 改成 reusable workflow：讓專案的 CI 直接呼叫這個 repo 裡的 workflow，改一次就全部生效。
