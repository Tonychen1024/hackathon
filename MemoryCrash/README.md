# Memory Crash - Game Framework

Cyberpunk Roguelike + Top Down Shooter + Stock Trading Simulation 的完整大型框架。

## 安裝方式

1. 進入專案資料夾：
   ```bash
   cd /home/runner/work/hackathon/hackathon/MemoryCrash
   ```
2. 建立虛擬環境（選用）：
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. 安裝依賴：
   ```bash
   pip install pygame
   ```

## 執行方式

```bash
python main.py
```

## 遊戲流程架構

- **Menu Scene** → 按 Enter 開始
- **Level Scene** → 關卡流程與地圖渲染
- **Market Scene** → 買賣股票、觸發新聞事件與價格波動
- **Boss Scene** → 該章 Boss 戰
- 完成 Boss 後進入下一章，共 5 章，最後進入完成畫面

## 目錄與系統說明

- `core/`
  - `scene_manager.py`: 場景切換系統（Menu/Level/Market/Boss）
  - `game_state.py`: Runtime/Save 資料結構
  - `event_system.py`: 事件訂閱發布
  - `save_system.py`: 存檔/讀檔（玩家資產、股票、解鎖關卡、最高分）
- `player/`
  - `player.py`: Player 主體（hp、damage、speed、money、inventory、stocks）
  - `weapon.py` / `skill.py`: 武器與技能框架
- `enemy/`
  - `enemy.py`: Enemy 基底（move/attack/take_damage/drop_memory）
  - `enemy_types.py`: 一般敵人類型
  - `boss.py`: 五大章 Boss 框架
- `market/`
  - `stock.py`: Stock（name、price、history、volatility、effect）
  - `market.py`: buy/sell/update_price/random_event
  - `news.py`: 假新聞/市場事件框架
- `levels/`
  - `level_manager.py`: Level 介面（load/update/draw/complete）與章節管理
  - `level_01.py` ~ `level_05.py`: 五章配置
- `maps/`
  - 五種記憶地圖骨架與 pygame primitive 渲染
- `ui/`
  - `hud.py`: 戰鬥 HUD
  - `market_ui.py`: 交易 UI
  - `boss_ui.py`: Boss UI

## 框架狀態

目前版本完成：

1. 完整遊戲流程骨架
2. 五大關卡切換
3. 市場系統框架
4. Boss 框架
5. UI 框架

採用 pygame primitive（rectangle / circle / text）建立，便於後續逐步替換為正式美術與玩法細節。
