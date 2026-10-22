# engineering-playbook

一個人加上 AI agent 開發軟體時的工作方法，加上一個可以直接複製的初始 repo。不綁定程式語言。

| 路徑 | 內容 |
|---|---|
| [`PLAYBOOK.md`](PLAYBOOK.md) | 這套系統的需求：每個做法要保證什麼、為什麼、什麼時候改（第 0～7 章）。修改系統或第一次採用時讀，日常開發不用讀 |
| [`starter/`](starter/) | 示範性的初始 repo，開新專案時整包複製 |
| [`tests/`](tests/) | `trace_check.py`、`spec-check.sh` 和 starter 設定的自我測試 |

## 平常你只做兩件事

決定要做什麼（開 Issue、排 roadmap）之後，每個會改變行為的功能，你只要做兩個決定：

1. **認可 spec**：規格作者開好 draft PR 後，看裡面 spec 的 diff；同意的話，執行它準備好的推送指令，輸入你的 SSH 密碼。
2. **合併**：看完審查者的回報，執行它準備好的合併指令。

不改變行為的 PR（錯字、文件、重構、套件更新）只有第 2 件。這兩件是 agent 做不到的：它們用的是 bot 帳號，推不動認可版本，也不能合併。其餘的 Git 操作，包括同步、比對和準備指令，都由 agent 照 `skills/` 執行。有標 `(manual)` 的 requirement 時，發版前還要照清單在實機上驗收（第 1 章）。

## 開新專案

這一節可以直接交給 agent 執行。在新專案的資料夾開一個 session，說一行就好，例如：

> 照 `<這個 repo 的路徑>/README.md` 的「開新專案」建立專案。專案是：〈一句話〉。

從既有產品遷移的話，再加上：從〈路徑〉的〈commit〉遷移。agent 在 push、建立 GitHub repo 或改任何 GitHub 設定之前，要先停下來給你看；用瀏覽器登入帳號、輸入 SSH 密碼，只能你自己做。這一節在第 8 步設好 bot 之前，都用你的帳號進行；設好之後，所有 agent 才一律用 bot（`AGENTS.md` 的 Roles）。

1. 複製 starter，建立 git repo：
   ```bash
   cp -R starter ../my-app && cd ../my-app && git init -b main
   ```
2. 第 0 章：確認這是會長期維護的產品（starter 照這個等級設計），填好 `docs/adr/0001-follow-engineering-playbook.md`，並記下這份 playbook 的 commit。
3. 選技術：填好 `scripts/check.sh`（測試結果輸出成 JUnit XML 到 `reports/junit/`），並在 `.github/workflows/ci.yml` 加上工具鏈的 setup 步驟。還沒有任何 app 時（例如從空資料夾開始，之後才把程式搬進來），工具那一段先換成一行 `echo`，保留檔案上方的 `trap`。
4. 填好 `README.md` 和 `AGENTS.md` 裡的專案說明和指令。驗收測試預設放在 `tests/acceptance/`，已附 `.gitkeep`；只有測試工具找不到那裡時（例如 monorepo 裡每個 app 各有自己的測試設定），才改 `AGENTS.md` 的 Acceptance tests 那一行。把 `skills/` symlink 到你用的 agent 工具讀 skill 的位置（第 1 章）。review 的 spec 檢查需要 Git 2.43 以上。
5. 從既有產品遷移時：在 ADR 0001 記下來源的路徑和 commit，並在 `AGENTS.md` 加一段 Migration：規格作者到哪裡找舊的 spec（只當參考，要對照現有的程式和測試確認），實作者拿哪份程式碼當參考（只搬 spec 要求的部分）。
6. 建立 GitHub repo 並 push，執行 `bash scripts/setup-github.sh`。這時 gh 預設登入的還是你。
7. 寫好 `docs/roadmap.md` 的目標和 Not doing。
8. 設定兩個身分（第 3 章第 2 點）：agent 一律用 bot，只有你做得到的事由你親手做。
   - 把 bot 加成 collaborator，再用 bot 接受邀請。
   - 先另外登入一份只給你用的 gh 設定：`GH_CONFIG_DIR=~/.config/gh-owner gh auth login`。之後合併和 `setup-github.sh` 都用它。
   - 再讓 gh 預設登入 bot（`gh auth login`，用瀏覽器以 bot 登入），然後把你的帳號從預設設定登出：`gh auth logout -u <你的帳號>`。不登出的話，agent 用 `gh auth switch` 就能換回你。
   - 執行一次 `gh auth setup-git`，讓 git 走 https 時也用 bot。不做的話，git 會從系統的憑證管理（例如 macOS 鑰匙圈）拿你的帳號。
   - 在專案加一個用你 SSH key 的 remote：`git remote add owner git@github.com:<你的帳號>/<repo>.git`。key 要有密碼，而且不要加進 ssh-agent 或鑰匙圈，這樣每次推送都要你輸入密碼。
   - 做完第 3 章的六項驗證。需要時再建 GitHub Project（第 1、3 章）。
9. 第一個功能開始時，照第 1 章的流程寫第一份 spec。

也可以把 `starter/` 推成一個獨立的 repo，在 GitHub 上設成 template repository，之後用 `gh repo create my-app --template <owner>/<repo> --clone` 開新專案。starter 的 CI 在 template repository 本身不會執行。

## 修改這份 playbook

- 改到某個保證或決定（要成立什麼、為什麼）時，同一個 commit 要更新 `PLAYBOOK.md` 對應的章節。只改指令或步驟的寫法時，只動 skills 或腳本，不用動 PLAYBOOK。
- 自我測試：`python3 -m unittest discover -s tests -v`，CI 也會跑。
- 已經複製出去的專案不會自動更新。等有兩個以上的專案、同一個檔案已經改過兩次，再把 CI 改成 reusable workflow：讓專案的 CI 直接呼叫這個 repo 裡的 workflow，改一次就全部生效。
