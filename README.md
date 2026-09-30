# engineering-playbook

一個人加上 AI agent 開發軟體時的工作方法，加上一個可以直接複製的初始 repo。不綁定程式語言。

| 路徑 | 內容 |
|---|---|
| [`PLAYBOOK.md`](PLAYBOOK.md) | 8 個問題（第 0～7 章），每一章都有預設答案、對應的模板、什麼時候要改 |
| [`starter/`](starter/) | 示範性的初始 repo，開新專案時整包複製 |
| [`tests/`](tests/) | `trace_check.py` 和 starter 設定的自我測試 |

## 開新專案

1. 複製 starter，建立 git repo：
   ```bash
   cp -R starter ../my-app && cd ../my-app && git init -b main
   ```
2. 第 0 章：決定嚴格程度，填好 `docs/adr/0001-follow-engineering-playbook.md`，並記下這份 playbook 的 commit。
3. 選技術：填好 `scripts/check.sh`（測試結果輸出成 JUnit XML 到 `reports/junit/`），並在 `.github/workflows/ci.yml` 加上工具鏈的 setup 步驟。
4. 填好 `README.md` 和 `AGENTS.md` 裡的專案說明和指令；把 `skills/` symlink 到你用的 agent 工具讀 skill 的位置（第 1 章）。
5. 建立 GitHub repo 並 push，套用 ruleset，做完兩個驗證（第 3 章）。
6. 寫好 `docs/roadmap.md` 的目標和 Not doing；把實作者的 bot 帳號加成 collaborator。需要時再建 GitHub Project（第 1、3 章）。
7. 第一個功能開始時，照第 1 章的流程寫第一份 spec。

也可以把 `starter/` 推成一個獨立的 repo，在 GitHub 上設成 template repository，之後用 `gh repo create my-app --template <owner>/<repo> --clone` 開新專案。starter 的 CI 在 template repository 本身不會執行。

## 修改這份 playbook

- 改 `starter/` 裡的檔案時，同一個 commit 要更新 `PLAYBOOK.md` 對應的章節。
- 自我測試：`python3 -m unittest discover -s tests -v`，CI 也會跑。
- 已經複製出去的專案不會自動更新。等有兩個以上的專案、同一個檔案已經改過兩次，再把 CI 改成 reusable workflow：讓專案的 CI 直接呼叫這個 repo 裡的 workflow，改一次就全部生效。
