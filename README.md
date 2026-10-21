# Live Football Betting Simulation Engine & Dashboard

A real-time, terminal-and-web sports betting simulation system built with Python and Vanilla JavaScript. The system ingests match data from a predictive analysis dataset, streams simulated wagers row-by-row into an active ledger (`custom_bets.csv`), enables concurrent user bet placement during a 60-second live window, and automatically computes settlements and net profit/loss into `filtered.csv`.

---

## Architecture Overview

```text
+---------------------------------------------+
| sports_betting_predictive_analysis.csv      |
+---------------------------------------------+
                       |
                       v
         [ generate_bets.py / Engine ]
                       |
                       +--> custom_bets.csv (Active Raw Bets Ledger)
                                   |
         +-------------------------+-------------------------+
         |                                                   |
         v                                                   v
[ Terminal Engine: stream_engine.py ]            [ Web Dashboard: index.html ]
- Multi-threaded timer (60s window)              - "Search for matches" fetch trigger
- Paced ticker (1 bet / 2.5s)                    - Live 60-second countdown bar
- In-place HUD (\r stdout refresh)               - Live order placement (user_me)
- Non-blocking CLI bet entry                     - Automated P&L reconciliation
                                                 - filtered.csv download