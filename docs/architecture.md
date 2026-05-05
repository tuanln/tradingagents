# TradingAgents — Tài liệu Kiến trúc & Mô hình Phản biện chéo

> Tài liệu này: (1) mô tả kiến trúc hệ thống TradingAgents, (2) phân tích ưu điểm
> của mô hình **agent phản biện chéo** (cross-debate), và (3) trình bày bản thiết
> kế áp dụng mô hình này cho một bài toán hoàn toàn khác — **R&D đội agent
> nghiên cứu sân vận động thông minh theo tiêu chuẩn FIFA**.

---

## Phần I — Kiến trúc TradingAgents

### 1. Tổng quan

TradingAgents là một framework giao dịch tài chính dùng nhiều LLM-agent, mô phỏng
cấu trúc của một sàn giao dịch thực tế: analyst → researcher → trader →
risk → portfolio manager. Toàn bộ luồng được orchestrate bằng **LangGraph**
(`tradingagents/graph/setup.py`), với state chia sẻ là `AgentState`
(`tradingagents/agents/utils/agent_states.py`).

### 2. Sơ đồ luồng

```
                          ┌────────────────────────────────┐
                          │        ANALYST TEAM            │
                          │  (tool-calling, song song)     │
                          ├────────────────────────────────┤
START ──► Market Analyst ─┤  market_report                 │
          Social Analyst ─┤  sentiment_report              │
          News Analyst   ─┤  news_report                   │
          Fundamentals   ─┤  fundamentals_report           │
                          └───────────────┬────────────────┘
                                          ▼
                          ┌────────────────────────────────┐
                          │       RESEARCHER TEAM          │
                          │   (debate Bull ↔ Bear N vòng)  │
                          └───────────────┬────────────────┘
                                          ▼
                          ┌────────────────────────────────┐
                          │       RESEARCH MANAGER         │
                          │  (trọng tài → ResearchPlan)    │
                          └───────────────┬────────────────┘
                                          ▼
                          ┌────────────────────────────────┐
                          │           TRADER               │
                          │  (đề xuất transaction concrete)│
                          └───────────────┬────────────────┘
                                          ▼
                          ┌────────────────────────────────┐
                          │       RISK MANAGEMENT          │
                          │  Aggressive ↔ Neutral ↔        │
                          │  Conservative (3 góc nhìn)     │
                          └───────────────┬────────────────┘
                                          ▼
                          ┌────────────────────────────────┐
                          │      PORTFOLIO MANAGER         │
                          │   (rating cuối: Buy/.../Sell)  │
                          └───────────────┬────────────────┘
                                          ▼
                                         END
```

### 3. Bốn lớp agent

| Lớp | Agents | Nhiệm vụ | Output trong `AgentState` |
|---|---|---|---|
| **Analyst Team** | Market, Social, News, Fundamentals | Tool-calling, thu thập dữ liệu thô và viết báo cáo prose | `market_report`, `sentiment_report`, `news_report`, `fundamentals_report` |
| **Researcher Team** | Bull, Bear | Tranh luận N vòng (config `max_debate_rounds`) trên cùng 4 báo cáo | `investment_debate_state.history` |
| **Decision Layer** | Research Manager → Trader | Trọng tài hoá debate thành plan có cấu trúc, rồi diễn dịch thành lệnh giao dịch | `investment_plan`, `trader_investment_plan` |
| **Risk Layer** | Aggressive ↔ Neutral ↔ Conservative → Portfolio Manager | Tranh luận rủi ro 3 phía, PM ra phán quyết cuối | `risk_debate_state`, `final_trade_decision` |

### 4. Cơ chế kỹ thuật cốt lõi

- **State machine có điều kiện** — `ConditionalLogic.should_continue_debate`
  (`graph/conditional_logic.py:46-55`) đếm số lượt và chuyển nhóm Bull→Bear→Bull
  cho đến khi đạt `2 × max_debate_rounds`, sau đó nhường sàn cho Research Manager.
- **Structured output** — 3 agent ra quyết định (Research Manager, Trader,
  Portfolio Manager) dùng Pydantic schemas (`agents/schemas.py`) để bảo đảm
  output có rating thuộc tập 5 mức (Buy/Overweight/Hold/Underweight/Sell), thay
  vì để LLM trả prose tự do dễ trôi format.
- **Two-tier LLM** — `deep_thinking_llm` cho 3 vai phán quyết, `quick_thinking_llm`
  cho phần còn lại (`graph/setup.py:78-87`) — tối ưu chi phí.
- **Persistent memory** — `TradingMemoryLog` lưu mọi quyết định kèm realised
  return + alpha vs SPY; lần chạy sau cùng ticker sẽ inject reflection vào prompt
  của Portfolio Manager (`README.md:227-231`).
- **Checkpoint resume** — LangGraph SqliteSaver per-ticker
  (`graph/checkpointer.py`); crash giữa chừng có thể resume từ node thành công
  cuối cùng.

---

## Phần II — Ưu điểm của mô hình "Agent phản biện chéo"

Mô hình **phản biện chéo (cross-debate / adversarial collaboration)** là điểm
khác biệt cốt lõi của TradingAgents so với các pipeline LLM tuyến tính một
chiều. Hệ thống dùng nó ở **hai vị trí**:

1. **Bull ↔ Bear** ở tầng researcher — debate 2 phía về *quan điểm đầu tư*.
2. **Aggressive ↔ Neutral ↔ Conservative** ở tầng risk — debate 3 phía về
   *khẩu vị rủi ro*.

### 1. Khử confirmation bias trong LLM

LLM đơn lẻ có xu hướng *ngụy biện một chiều*: cho ngữ cảnh mơ hồ thì sẽ chọn
một narrative rồi cherry-pick bằng chứng để củng cố nó. Bull/Bear buộc mô hình
**phải tạo ra hai cây luận chứng đối lập** từ cùng một bộ dữ liệu, sau đó
trọng tài chọn cây mạnh hơn — nhờ vậy bằng chứng yếu sẽ lộ rõ.

### 2. Falsifiability — "không đối lập được = không đáng tin"

Trong `bull_researcher.py:21` và `bear_researcher.py:22`, prompt yêu cầu
mỗi bên **trực tiếp phản pháo (counterpoint)** lập luận đối phương, không
được chỉ liệt kê data. Điều này đẩy tranh luận sang tiêu chí khoa học của
Popper: nếu một luận điểm không bị bên kia đối lập được, nó được coi là
robust; nếu sụp đổ trước counterpoint, tự khắc bị loại.

### 3. Search-space lớn hơn so với chain-of-thought đơn

Một CoT đơn duyệt một nhánh suy luận. Hai agent đối lập duyệt **hai nhánh
ngược dấu**, hợp thành cây tìm kiếm rộng hơn 2× với cùng số token — tăng khả
năng chạm tới luận điểm thiểu số nhưng đúng (rare-but-correct edge cases).

### 4. Phân vai → tách nhập nhằng giữa "chứng cứ" và "phán quyết"

- Analysts: chỉ cung cấp **dữ kiện**.
- Researchers (Bull/Bear): chỉ **diễn giải** dữ kiện thành luận điểm.
- Manager: chỉ **trọng tài**, không tự sinh dữ kiện mới.

Mỗi agent có một mục tiêu hẹp → prompt ngắn, ít drift, dễ debug. Nếu sai, ta
biết sai ở tầng nào (dữ liệu? diễn giải? phán quyết?).

### 5. Multi-perspective ở tầng risk: 3-way debate

Bull/Bear là nhị phân, dễ rơi vào *false dichotomy*. Tầng risk đối phó bằng
3 góc nhìn (Aggressive/Neutral/Conservative) — bắt buộc tranh luận xoay vòng
3-way (`conditional_logic.py:57-67`), giảm rủi ro hai phe cực đoan đồng thuận
mà bỏ qua trung dung hợp lý.

### 6. Auditability & regulatory friendliness

Mọi vòng debate được lưu vào `investment_debate_state.history` và dump JSON
(`graph/trading_graph.py:359-369`). Một regulator có thể truy ngược: *quyết
định Sell này dựa trên lập luận nào của Bear, lập luận đó đã bị Bull phản
pháo ra sao, vì sao Manager vẫn chọn Bear?* — điều mà output của một LLM đơn
gần như không cho phép.

### 7. Robust hơn trước nhiễu prompt-injection

Nếu một analyst report bị nhiễm prompt injection (vd: news bị bot bơm tin
giả tích cực), Bear researcher sẽ tấn công luận điểm tích cực đó bằng các
nguồn khác → manager có cơ hội phát hiện inconsistency thay vì xuôi theo
tin giả.

### 8. Trade-off cần lưu ý

| Ưu | Nhược |
|---|---|
| Bằng chứng đối kháng, ít confirmation bias | Token cost ~2-3× so với pipeline đơn |
| Output có audit trail rõ | Latency cao hơn (debate phải tuần tự) |
| Sửa prompt 1 phía không phá phía kia | Có thể "echo chamber" nếu cả 2 phía dùng cùng base model với cùng training bias |
| Trọng tài có thể được swap (LLM khác/người) | Trọng tài LLM vẫn là single point of failure |

**Mitigation:** dùng `deep_thinking_llm` (mạnh hơn) cho trọng tài, dùng
`quick_thinking_llm` (rẻ hơn) cho debate; cấu hình cho phép đặt provider khác
nhau cho 2 tầng.

---

## Phần III — Đề xuất đội agent: R&D Sân vận động thông minh chuẩn FIFA

Áp dụng cùng triết lý **phản biện chéo + phân vai chặt** của TradingAgents vào
một bài toán nghiên cứu hoàn toàn khác.

### 1. Bài toán

Nghiên cứu, tổng hợp tài nguyên toàn cầu về **sân vận động thông minh
(smart stadium)** đáp ứng tiêu chuẩn FIFA (FIFA Stadium Guidelines, FIFA
Quality Programme), phân tích:
- Giải pháp công nghệ của các nhà cung cấp lớn.
- Rủi ro triển khai và vận hành.
- Ngân sách dự kiến (CapEx + OpEx).
- Khả năng mở rộng / tương lai 5–10 năm.

### 2. Domain breakdown — 6 trục công nghệ chính

Theo các tài liệu FIFA Stadium Guidelines (an toàn khán giả, broadcast HDR/4K,
hệ thống chiếu sáng FIFA Quality, mặt cỏ, accessibility):

| # | Trục | Phạm vi |
|---|---|---|
| T1 | **Connectivity & Network** | Wi-Fi 6/7 mật độ cao, 5G in-stadium, neutral host DAS, fiber backbone |
| T2 | **Broadcast & Media** | Camera 4K/8K HDR, slow-mo, cabling, IP production (SMPTE 2110), VAR infra |
| T3 | **Fan Experience** | App, AR/VR, ticketing NFC, cashless concession, wayfinding, second-screen |
| T4 | **Safety & Security** | CCTV AI analytics, crowd density, biometric access, drone defense, BMS tích hợp PCCC |
| T5 | **Pitch & Facility** | Hybrid grass (SISGrass/Desso), pitch heating, lighting LED FIFA Quality Pro, irrigation IoT |
| T6 | **Sustainability & Energy** | Solar canopy, BESS, water reuse, BREEAM/LEED, carbon accounting |

### 3. Kiến trúc đội agent đề xuất

```
                        ┌──────────────────────────────────────┐
                        │          DOMAIN ANALYSTS             │
                        │     (1 agent / trục × 6 trục)        │
                        └──────────────────────────────────────┘
                                    │
                                    ▼
                        ┌──────────────────────────────────────┐
                        │  STANDARDS COMPLIANCE ANALYST        │
                        │  (FIFA / IEC / ISO / IBC mapping)    │
                        └──────────────────────────────────────┘
                                    │
                                    ▼
                        ┌──────────────────────────────────────┐
                        │         R&D DEBATE TEAM              │
                        │  Innovator ↔ Sceptic ↔ Pragmatist    │
                        │      (3-way, N vòng)                 │
                        └──────────────────────────────────────┘
                                    │
                                    ▼
                        ┌──────────────────────────────────────┐
                        │       VENDOR MAPPING ANALYST         │
                        │   (so sánh giải pháp các bên)        │
                        └──────────────────────────────────────┘
                                    │
                                    ▼
                        ┌──────────────────────────────────────┐
                        │        RISK DEBATE TEAM              │
                        │ Tech Risk ↔ Financial Risk ↔         │
                        │ Operational Risk ↔ Geo/Regulatory    │
                        │      (4-way, N vòng)                 │
                        └──────────────────────────────────────┘
                                    │
                                    ▼
                        ┌──────────────────────────────────────┐
                        │     BUDGET & ROADMAP MANAGER         │
                        │  (CapEx + OpEx + 5-10y scaling plan) │
                        └──────────────────────────────────────┘
                                    │
                                    ▼
                        ┌──────────────────────────────────────┐
                        │       EXECUTIVE EDITOR (PM)          │
                        │   (white paper + go/no-go rating)    │
                        └──────────────────────────────────────┘
```

### 4. Mô tả từng agent

#### 4.1 Domain Analysts (T1–T6)

6 agent song song, mỗi agent phụ trách một trục công nghệ. Mỗi agent có **bộ
tool riêng**:

| Agent | Tools |
|---|---|
| Connectivity Analyst | `web_search("Wi-Fi 6E stadium deployment")`, `fetch_spec(IEEE 802.11ax)`, `fetch_fifa_doc(connectivity guidelines)` |
| Broadcast Analyst | `web_search("SMPTE 2110 stadium")`, `fetch_uefa_broadcast_brief`, `vendor_db("Sony / Grass Valley / EVS")` |
| Fan-Experience | `web_search("stadium app case study")`, `appstore_lookup`, `case_study_db` |
| Safety & Security | `fetch_iso(IEC 62676)`, `fetch_fifa_safety`, `web_search("crowd analytics deployment")` |
| Pitch & Facility | `fetch_fifa_quality_pro_lighting`, `fetch_sisgrass_spec`, `web_search("LED pitch lighting 2000+ lux")` |
| Sustainability | `fetch_breeam`, `fetch_leed`, `web_search("solar canopy stadium kWh")`, `carbon_db` |

Output: `domain_report_T{1..6}` (markdown), bắt buộc có bảng *State of the
Art / FIFA requirement / Gap* ở cuối — tương tự pattern báo cáo có Markdown
table cuối ở `fundamentals_analyst.py:28`.

#### 4.2 Standards Compliance Analyst

Đọc 6 báo cáo trên, **map mỗi giải pháp công nghệ vào các tiêu chuẩn**:
- FIFA Stadium Guidelines, FIFA Quality Programme (lighting, pitch, ball).
- FIFA World Cup Technical Recommendations (broadcast, accessibility).
- IEC 60364, EN 50132 (security CCTV), IEC 62305 (lightning).
- ISO 14001 (env), ISO 27001 (info-sec), ISO 20121 (sustainable events).
- Local: IBC/IFC fire code, building code nước sở tại.

Output: `standards_matrix` — bảng tiêu chuẩn × giải pháp, đánh dấu compliant /
gap / unknown.

#### 4.3 R&D Debate Team — phản biện chéo 3-way (đặc trưng cốt lõi)

Đây chính là *bản đồng dạng* của Bull/Bear ở TradingAgents, nhưng mở rộng
lên 3 phía vì nghiên cứu R&D có nhiều trục đánh đổi hơn quyết định mua/bán:

| Agent | Vai | Prompt tinh thần |
|---|---|---|
| **Innovator** | Đẩy state-of-the-art | "Đề xuất giải pháp tiên tiến nhất; nhấn mạnh upside competitive, mass-experience, branding global" |
| **Sceptic** | Đánh đổ giả định | "Tìm điểm yếu, vendor hype, immature tech, TRL < 7, single-vendor lock-in, kết quả case study cherry-picked" |
| **Pragmatist** | Triển khai-được | "Cân nhắc khả thi: ngân sách, đội vận hành, thời gian thi công, tương thích sân hiện hữu, độ rủi ro pháp lý địa phương" |

Mỗi vòng: Innovator phát biểu → Sceptic counter → Pragmatist hoà giải → lặp
N vòng. Cơ chế tương tự `should_continue_risk_analysis`
(`conditional_logic.py:57-67`).

**Tại sao 3-way chứ không 2-way như Bull/Bear?** Bài toán R&D có 3 trục đối
kháng tự nhiên (innovation ↔ rigour ↔ feasibility), không thuần nhị phân;
3-way debate tránh false dichotomy đã nói ở Phần II §5.

#### 4.4 Vendor Mapping Analyst

Đầu ra debate trên là *yêu cầu giải pháp*. Agent này **map yêu cầu → các
bên cung cấp thực tế** trên thị trường:

- Connectivity: Cisco, HPE Aruba, Extreme Networks, Huawei, Boldyn (DAS).
- Broadcast: Sony, Grass Valley, EVS, Hawk-Eye, Chyron, Riedel.
- Fan App / Ticketing: VenueNext, SeatGeek, Tappit, Ticketmaster, Mastercard.
- Safety AI: Genetec, Avigilon, Bosch, Hikvision (lưu ý geopolitical).
- Pitch: SISGrass, Desso GrassMaster, Hellas, Mondo (lighting LED).
- Sustainability: Schneider Electric, Siemens, ABB, Tesla Megapack.

Output: `vendor_matrix` — một bảng so sánh ưu/nhược/giá tham khảo/case study
gần đây/level of vendor lock-in.

#### 4.5 Risk Debate Team — phản biện chéo 4-way

Lấy cảm hứng từ Aggressive/Neutral/Conservative nhưng mở rộng lên 4 phía
vì rủi ro của một dự án sân vận động trải rộng:

| Agent | Quan tâm |
|---|---|
| **Tech Risk** | Vendor lock-in, tech obsolescence, integration failure, cyber attack surface |
| **Financial Risk** | CapEx overrun, FX, lãi suất, ROI ticketing/sponsorship không đạt |
| **Operational Risk** | Staffing, maintenance SLA, downtime ngày matchday, supply-chain spare-part |
| **Geopolitical / Regulatory** | Sanction (vd Hikvision), data sovereignty (GDPR/CCPA), local content requirement, FIFA bid commitment |

Mỗi agent có `must_engage_with_others = True` — bắt buộc trích dẫn ít nhất
1 luận điểm của các phía khác và phản bác → ép cross-pollination, tránh các
silo tự nói với mình.

#### 4.6 Budget & Roadmap Manager

Tổng hợp toàn bộ → ra **bản tài chính có cấu trúc**, schema Pydantic
tương tự `PortfolioDecision` ở `agents/schemas.py:171-206`:

```python
class StadiumBudgetPlan(BaseModel):
    capex_breakdown: dict[str, float]      # USD theo trục T1..T6
    opex_yearly: dict[str, float]          # USD/năm theo hạng mục
    capex_total_low: float                  # khoảng confident thấp
    capex_total_high: float                 # khoảng confident cao
    payback_years: float
    roadmap_phases: list[Phase]             # phase 0/1/2/3, có gating
    scaling_5y: str                          # mở rộng 5 năm
    scaling_10y: str                         # mở rộng 10 năm
    confidence: Literal["low","medium","high"]
```

#### 4.7 Executive Editor (Portfolio Manager analogue)

Vai cuối cùng — đóng gói toàn bộ thành **white paper** + đưa rating
go/no-go/conditional-go cho từng trục công nghệ. Rating scale 5 mức tương
tự `PortfolioRating`:

```
Adopt | Pilot | Hold | Defer | Reject
```

Mỗi trục có rating riêng + executive summary + bảng dependency
(T1 Connectivity là tiền đề của T3 Fan Experience, v.v.).

### 5. Bảng tham chiếu ngân sách (mức tham khảo định hướng)

> **Lưu ý:** giá trị dưới đây là *order-of-magnitude* dựa trên dữ liệu công
> khai về các sân World Cup 2022 (Qatar), 2026 (US/Can/Mex), Premier League
> & UEFA Cat.4 mới gần đây. **Phải được Budget & Roadmap Manager refine theo
> bối cảnh dự án cụ thể**, không dùng làm con số commit.

| Trục | CapEx tham chiếu (USD) | OpEx/năm (USD) | Ghi chú |
|---|---|---|---|
| T1 Connectivity | 8–25 M | 0.5–1.5 M | Phụ thuộc sức chứa & DAS có sẵn |
| T2 Broadcast | 15–60 M | 1–3 M | UHD/HDR đẩy chi phí lên đáng kể |
| T3 Fan Experience | 5–15 M | 1–2 M | App + ticketing + AR; tích hợp CRM |
| T4 Safety & Security | 10–30 M | 2–4 M | AI analytics + integration BMS |
| T5 Pitch & Facility | 8–20 M | 1–2 M | Hybrid grass + LED Class A |
| T6 Sustainability | 10–40 M | (tiết kiệm 1–3 M) | Solar + BESS có payback 7–12 năm |
| **Tổng CapEx** | **56–190 M USD** | **5.5–13.5 M/năm** | Sân Cat.4 / FIFA-ready 40k–60k chỗ |

### 6. Rủi ro chiến lược cần tracking liên tục

1. **Tech obsolescence** — Wi-Fi 7 / 8K / Ar Ad-tech: chu kỳ refresh 5–7 năm.
2. **Vendor lock-in** — đặc biệt mảng broadcast IP và CCTV AI; ưu tiên vendor
   tuân thủ chuẩn mở (SMPTE 2110, ONVIF Profile T).
3. **Cybersecurity surface** — mọi IoT field device là điểm tấn công; cần
   segment network + zero-trust architecture.
4. **Geopolitical** — sanction đối với một số vendor Châu Á; cần plan B.
5. **Regulatory drift** — GDPR + AI Act EU + biometric law từng nước có thể
   khoá tính năng face-recognition giữa vòng đời.
6. **Climate risk** — heatwave làm tăng OpEx HVAC; tropical storm với sân
   ven biển; phải design-for-resilience ngay CapEx.
7. **Match-day operational risk** — downtime giờ trận = vi phạm SLA broadcast,
   thiệt hại nhiều triệu USD/sự kiện.
8. **Stakeholder risk** — FIFA/AFC/local FA có yêu cầu khác biệt; bid
   commitment có thể đổi sau khi trao quyền đăng cai.

### 7. Tầm nhìn mở rộng 5–10 năm

| Thời điểm | Khả năng mở rộng |
|---|---|
| **5 năm** | Wi-Fi 7 phổ cập; 5G SA + network slicing cho VAR/broadcast; AI fan-engagement cá nhân hoá; full cashless; scope 1–2 net-zero |
| **7 năm** | XR/spatial-computing experience (Apple Vision Pro-like); pitch sensor toàn diện cho referee assist; digital twin vận hành |
| **10 năm** | 8K/12K HDR là default broadcast; volumetric capture cho replay 3D; autonomous concession & cleaning robot; net-positive energy; scope 3 reportable; tích hợp tokenized fan economy nếu khung pháp lý cho phép |

Roadmap nên thiết kế **modular từ đầu**: cabling oversize 30–50%, BMS có
open API, broadcast room có spare rack 30%, electrical risers oversize cho
EV charging và BESS tương lai.

### 8. Kế hoạch kỹ thuật triển khai đội agent (nếu code tiếp)

Trong codebase hiện tại có thể tổ chức như sau (giữ kiểu module của
`tradingagents/agents/`):

```
tradingagents/
└── stadium_rnd/                        # package song song
    ├── agents/
    │   ├── domain/
    │   │   ├── connectivity.py
    │   │   ├── broadcast.py
    │   │   ├── fan_experience.py
    │   │   ├── safety_security.py
    │   │   ├── pitch_facility.py
    │   │   └── sustainability.py
    │   ├── compliance/standards_analyst.py
    │   ├── debate/{innovator,sceptic,pragmatist}.py
    │   ├── vendor/vendor_mapping.py
    │   ├── risk/{tech,financial,operational,geopolitical}.py
    │   ├── managers/{budget_roadmap,executive_editor}.py
    │   └── schemas.py                  # Pydantic schemas tương tự agents/schemas.py
    ├── dataflows/
    │   ├── fifa_docs.py                # fetch FIFA guidelines
    │   ├── standards_db.py             # IEC/ISO/IBC reference
    │   ├── vendor_db.py
    │   └── case_study_search.py        # web_search adapters
    └── graph/
        ├── setup.py                    # đồng dạng tradingagents/graph/setup.py
        └── conditional_logic.py        # debate-rotation + risk 4-way
```

Bám sát các pattern hiện có:
- Tool-calling analyst → mượn `fundamentals_analyst.py:33-57`.
- Debate node → mượn `bull_researcher.py` + mở rộng 3-way từ
  `risk_mgmt/aggresive_debator.py` (cơ chế đếm vòng & xoay vai).
- Trọng tài có structured output → mượn `research_manager.py:13-48` +
  `agents/utils/structured.py` để bind Pydantic schema vào provider.
- State machine — định nghĩa `StadiumState(MessagesState)` đồng dạng
  `AgentState` ở `agents/utils/agent_states.py`.

---

## Phần IV — Đối chiếu nhanh hai hệ thống

| Khía cạnh | TradingAgents | Stadium R&D Agents (đề xuất) |
|---|---|---|
| Domain | Tài chính | Hạ tầng thể thao |
| Tần suất chạy | Mỗi ticker × ngày | Mỗi dự án × milestone |
| Đầu vào | Giá, news, fundamentals | FIFA docs, vendor specs, case study |
| Đầu ra | Buy/Hold/Sell | Adopt/Pilot/Hold/Defer/Reject × 6 trục + ngân sách |
| Phản biện chéo | Bull↔Bear (2-way), Risk 3-way | R&D 3-way, Risk 4-way |
| Memory | Realised return + reflection | Quyết định + outcome triển khai (cập nhật pha) |
| Trọng tài | Research Manager + Portfolio Manager | Budget Manager + Executive Editor |
| Audit trail | JSON state log | Tương tự — bắt buộc dump để cấp uỷ duyệt review |

Triết lý **phân vai chặt + phản biện chéo + structured output ở tầng quyết
định** giữ nguyên; chỉ thay nội dung tool, schema, và số chiều debate cho
phù hợp với domain mới.

---

## Phần V — Token Economics & Kiến trúc tối ưu (LangChain/LangGraph + Claude)

> Phần này trả lời 2 câu hỏi: **(a)** chạy đội agent này trên LangChain với
> backend Claude tốn bao nhiêu token, **(b)** thiết kế kiến trúc thế nào để
> mỗi khi đối tác nộp giải pháp mới chỉ phải trả "delta token" thay vì rerun
> toàn bộ.

### 1. Khung ước tính token

Mỗi node trong graph tiêu token theo 3 thành phần:

```
T_node = T_system + T_context + T_history + T_tool_io   (input)
       + T_output                                       (output)
```

| Thành phần | Mô tả | Đặc điểm tiêu thụ |
|---|---|---|
| `T_system` | System prompt cố định | Lặp lại mỗi lần gọi → **cache được** |
| `T_context` | FIFA docs, standards, vendor catalog | Lặp lại trong cùng phiên → **cache được** |
| `T_history` | Báo cáo các analyst trước + lịch sử debate | Tăng dần theo node → tốn nhất |
| `T_tool_io` | Kết quả `web_search`, `fetch_doc` | Có thể rất lớn (PDF, spec) → cần *trim & retrieve* |
| `T_output` | Báo cáo / luận điểm / schema | Phụ thuộc verbosity prompt |

### 2. Baseline (chưa tối ưu) — 1 lần phân tích dự án sân vận động

Giả định: 6 domain analyst, compliance, R&D-debate 3-way × 2 vòng (6 lượt),
vendor mapping, risk-debate 4-way × 1 vòng (4 lượt), budget manager,
executive editor.

| Node | Input (tok) | Output (tok) | Ghi chú |
|---|---:|---:|---|
| 6 × Domain Analyst | 6 × 30k = 180k | 6 × 3k = 18k | Có tool-calling, ngữ cảnh là FIFA spec |
| Standards Compliance | 60k | 4k | Đọc 6 báo cáo |
| R&D Debate (6 lượt × 60k) | 360k | 12k | Mỗi lượt nhồi cả 6 báo cáo + history |
| Vendor Mapping | 80k | 4k | Vendor catalog là bulk text |
| Risk Debate (4 lượt × 80k) | 320k | 8k | Đọc cả vendor matrix |
| Budget & Roadmap Manager | 120k | 5k | Tổng hợp chi tiết |
| Executive Editor | 150k | 6k | White paper output |
| **Tổng** | **~1.27 M** | **~57 k** | |

**Chi phí baseline với một mô hình đồng nhất (giá tham chiếu Claude tháng
2026, để xác minh trên trang pricing trước khi commit budget):**

| Mô hình | Input $/M | Output $/M | Chi phí 1 dự án |
|---|---:|---:|---:|
| Claude Haiku 4.5 | $1 | $5 | ~$1.6 |
| Claude Sonnet 4.6 | $3 | $15 | ~$4.7 |
| Claude Opus 4.7 | $15 | $75 | ~$23.3 |

**Hotspot:** debate là kẻ đốt token chính (~53% input cả run) vì mỗi lượt
nhồi lại toàn bộ báo cáo. Đây chính là chỗ cần tối ưu mạnh nhất.

### 3. Bảy lớp tối ưu (xếp theo ROI giảm dần)

#### Lớp 1 — Prompt caching gốc của Anthropic (đòn bẩy lớn nhất)

Anthropic hỗ trợ cache với `cache_control: {"type": "ephemeral"}` trên block
content; cache hit chỉ tính **10% giá input thường**, cache write tính
**125%**. TTL 5 phút (default) hoặc 1 giờ (opt-in).

Đặt **cache breakpoint** sau system + FIFA docs + 6 báo cáo analyst →
mọi lượt debate sau đó chỉ trả 10% giá cho phần *prefix*, chỉ trả full giá
cho phần *history* mới phát sinh.

```python
# LangChain — ChatAnthropic
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-6")
messages = [
    SystemMessage(content=[
        {"type": "text", "text": SYSTEM_PROMPT},
        {"type": "text", "text": FIFA_REFERENCE_BUNDLE,
         "cache_control": {"type": "ephemeral"}},   # ← breakpoint
    ]),
    HumanMessage(content=[
        {"type": "text", "text": COMBINED_ANALYST_REPORTS,
         "cache_control": {"type": "ephemeral"}},   # ← breakpoint thứ 2
        {"type": "text", "text": current_debate_history},   # phần "tươi"
    ]),
]
```

Hiệu ứng kỳ vọng: 6 lượt debate cùng đọc 200k token prefix → lượt 1 trả
full, lượt 2-6 trả 10%. **Tiết kiệm ~70% input cho debate node**, giảm
tổng input từ 1.27M → ~0.5M.

#### Lớp 2 — Hierarchical summarization giữa các tầng

Truyền **bản tóm 1-2k token** sang tầng kế thay vì nguyên báo cáo:

```
Domain Analyst (T1..T6)  →  full report 3k tok mỗi cái
                ▼ summarize  (Haiku gọi nhanh)
            6 × 500 tok summary = 3k tok
                ▼
        Standards Compliance đọc summary, chỉ retrieve fulltext khi cần
```

Áp dụng cho: input vào R&D Debate, vào Risk Debate. Bản fulltext giữ trong
state nhưng *không nhồi prompt* — debate đọc summary; nếu cần trích chứng
cứ chi tiết, agent gọi tool `fetch_full_report(T_idx)` (RAG nội bộ).

Tiết kiệm: 60k → 6k context mỗi lượt debate → input debate giảm 10×.

#### Lớp 3 — Retrieval-Augmented Generation cho catalog tĩnh

FIFA Stadium Guidelines, IEC/ISO docs, vendor catalog là tài liệu *tĩnh,
khổng lồ*. Index một lần vào vector store (Chroma/Qdrant/PGVector), agent
truy vấn top-k chunk thay vì nhồi cả PDF.

```
fifa_docs/  →  embedding  →  vector store
                                  │
agent prompt: "FIFA lighting requirement for Cat.4 stadium" 
                                  │
                              top-3 chunks (1.5k tok)  →  prompt
```

Mỗi domain analyst tiết kiệm ~15-20k tok input mà không giảm chất lượng;
giảm hallucination về spec.

#### Lớp 4 — Model routing theo độ phức tạp (two/three-tier)

Mượn pattern `deep_thinking_llm` vs `quick_thinking_llm` của TradingAgents
(`graph/setup.py:78-87`), mở rộng 3 tầng:

| Tier | Model | Dùng cho |
|---|---|---|
| **Cheap** | Haiku 4.5 | Domain analysts, summarization, tool-call orchestration, vendor lookup |
| **Mid** | Sonnet 4.6 | Compliance, vendor mapping, R&D Debate, Risk Debate |
| **Deep** | Opus 4.7 | Budget & Roadmap Manager, Executive Editor (kết luận có rating) |

Phân bổ token typical sau khi áp tối ưu:

| Tier | Input | Output | Chi phí |
|---|---:|---:|---:|
| Haiku | 200k | 25k | $0.32 |
| Sonnet | 350k | 22k | $1.38 |
| Opus | 90k | 11k | $2.18 |
| **Tổng** | **640k** | **58k** | **~$3.88** |

Với caching ở Lớp 1: cache-read input ~400k × 10% giá = đáng kể, **chi phí
xuống ~$1.5–2.5 / dự án**.

#### Lớp 5 — Map-reduce thay round-robin debate

Round-robin (Bull → Bear → Bull) là tuần tự, mỗi lượt phải đọc lại lịch sử.
**Map-reduce variant**:

```
round 1 (parallel):
   Innovator   ─► luận điểm độc lập (đọc summary, không đọc bên kia)
   Sceptic     ─► luận điểm độc lập
   Pragmatist  ─► luận điểm độc lập
                │
                ▼  (reduce)
   Synthesizer  ─► chỉ ra điểm xung đột thực sự (10-15 điểm)
                │
                ▼
round 2 (parallel, focused):
   3 agent chỉ tranh luận trên ~10 điểm xung đột (context nhỏ)
```

So với round-robin 6 lượt × 60k = 360k input, map-reduce: 3 × 30k + 1 × 50k
+ 3 × 20k = ~200k input, **giảm ~45%**. Thêm bonus là chạy được parallel →
latency thấp hơn ~2-3×.

#### Lớp 6 — Stop-condition sớm cho debate

Trong `conditional_logic.py:46-55` debate dừng cứng theo `max_debate_rounds`.
Thêm cơ chế **early stopping**:

- Sau mỗi lượt, gọi judge LLM (Haiku, ngắn) trả `consensus_score ∈ [0,1]`.
- Nếu `consensus_score > 0.85` → bỏ qua các vòng còn lại, đi thẳng tới
  Research Manager.
- Nếu `< 0.3` (debate đang phân kỳ) → bắt buộc thêm 1 vòng có "moderator
  reframe".

Trên các case có dữ liệu rõ, debate thường hội tụ sau vòng 1; cắt vòng 2-3
tiết kiệm ~30-40% tokens cho ~50% case.

#### Lớp 7 — Batch API (cho phân tích offline)

Anthropic Message Batches API giảm **50% giá** cho job chấp nhận trễ ≤ 24h.
Phù hợp với:
- Re-analysis hàng loạt khi tiêu chuẩn FIFA cập nhật.
- So sánh 50 vendor solutions cuối quý.
- Reflection batch trên outcome dự án trong quá khứ.

Workflow realtime của partner mới vẫn dùng API thường; batch API chỉ cho
"sweep job".

### 4. Workflow phân tích **incremental** khi đối tác nộp giải pháp mới

Đây là use case chính bạn nêu: *"mỗi khi có giải pháp đối tác, đưa vào
phân tích tổng thể, chi phí, rủi ro tích hợp, mở rộng tương lai"*.

#### 4.1 Nguyên tắc

**Không rerun cả pipeline.** Tách state thành 2 phần:

```
PROJECT_STATE (long-lived, cached, versioned)
  ├─ fifa_reference_bundle      ─┐
  ├─ standards_matrix            │  cache 1h
  ├─ domain_reports[T1..T6]      │  với cache_control breakpoints
  ├─ vendor_matrix (current)     │
  └─ rolling_executive_summary  ─┘

SOLUTION_DELTA  (transient, mỗi lần partner submit)
  ├─ partner_id, solution_doc
  ├─ classified_axes[T_i, T_j, ...]
  ├─ delta_compliance
  ├─ delta_vendor_diff
  ├─ delta_debate_log
  ├─ delta_risk_assessment
  └─ delta_budget_impact
```

#### 4.2 Sub-graph "delta-analysis"

```
Partner submits solution
        │
        ▼
[1] Solution Classifier (Haiku)
        - Phân loại giải pháp thuộc trục T_i nào
        - Output: tag set, độ liên đới T_j ≠ T_i
        │
        ▼
[2] Spec Extractor (Haiku, tool-calling)
        - Bóc spec, KPI, giá tham khảo, scope
        - Cache PROJECT_STATE.fifa_reference_bundle
        │
        ▼
[3] Compliance Delta (Sonnet)
        - So với standards_matrix → flag pass/fail/unknown
        │
        ▼
[4] Focused R&D Debate 3-way (Sonnet, 1 vòng map-reduce)
        - Context CHỈ gồm: trục T_i + summary T_j liên đới (tổng <10k)
        - 3 agent đánh giá so với incumbent solution trong vendor_matrix
        │
        ▼
[5] Integration Risk Analyst (Sonnet)
        - Tương thích với 5 trục còn lại?
        - Vendor lock-in / cyber surface delta
        - Backward compat với phase đã build
        │
        ▼
[6] Budget Delta (Sonnet)
        - CapEx delta, OpEx delta, payback delta
        - Sensitivity ±20%
        │
        ▼
[7] Future-proof Scoring (Sonnet)
        - Roadmap 5y/10y compatibility
        - Modularity, open-standard score
        │
        ▼
[8] Executive Update (Opus)
        - Update rolling_executive_summary
        - Rating mới: Adopt/Pilot/Hold/Defer/Reject cho solution này
        - Update vendor_matrix nếu Adopt
```

#### 4.3 Token cost của 1 lần delta analysis

| Bước | Input | Output | Ghi chú |
|---|---:|---:|---|
| Classifier | 5k | 0.5k | Haiku |
| Spec Extractor | 20k | 2k | Haiku, kèm tool |
| Compliance Delta | 25k (cache hit) | 2k | Sonnet |
| Focused Debate | 40k (cache hit lớn) | 3k | Sonnet, 1 vòng |
| Integration Risk | 30k | 2k | Sonnet |
| Budget Delta | 25k | 2k | Sonnet |
| Future-proof | 20k | 1.5k | Sonnet |
| Exec Update | 60k | 4k | Opus |
| **Tổng** | **~225k** | **~17k** | |

**Sau khi áp Lớp 1 caching (~70% prefix là cache-hit):**

- Effective input: 75k full-priced + 150k × 10% = **90k tính giá**
- Output: 17k
- Chi phí với mix tier: **~$0.6 – 1.2 / 1 đối tác**

So với rerun toàn bộ pipeline (~$3-5): **giảm 75-85%**.

### 5. Dự phóng chi phí theo quy mô

Giả sử 1 dự án sân:
- 1 lần khởi tạo PROJECT_STATE (full pipeline).
- 30 đối tác nộp giải pháp lần đầu trong giai đoạn DD.
- 20 đối tác nộp lại bản revised.
- 4 lần "sweep re-analysis" theo quý (batch API).

| Hạng mục | # lần | Token in | Token out | Chi phí |
|---|---:|---:|---:|---:|
| Full pipeline khởi tạo (caching + multi-tier) | 1 | ~640k | ~58k | ~$2.5 |
| Delta analysis lần đầu | 30 | 30 × 90k effective | 30 × 17k | ~$24 |
| Delta analysis (revised, prefix cache nóng) | 20 | 20 × 60k eff | 20 × 12k | ~$12 |
| Sweep re-analysis (batch -50%) | 4 | 4 × 400k eff | 4 × 30k | ~$8 |
| **Tổng cho 1 dự án (1 năm)** | | | | **~$45–60** |

**Không tối ưu: cùng kịch bản tốn ~$200-400.** Khi scale lên nhiều dự án
sân (vd 5 sân hạng A song song), kiến trúc cache-friendly tiết kiệm hàng
nghìn USD/năm.

### 6. Lưu ý hiện thực hoá trên LangChain/LangGraph

#### 6.1 Cache breakpoint với `ChatAnthropic`

LangChain Anthropic adapter truyền `cache_control` qua content blocks.
Đặt breakpoint **sau** khối tĩnh nhất; tối đa 4 breakpoint/request.

#### 6.2 LangGraph state phải nhỏ

State quá lớn → mỗi node nhận snapshot full → token explosion. Dùng
**reducer + reference**:

```python
class ProjectState(TypedDict):
    domain_report_refs: dict[str, str]   # path/URI, KHÔNG inline text
    standards_matrix_ref: str
    rolling_summary: str                  # cập nhật hierarchical
    delta_solution_active: SolutionDelta # solution đang xử lý
```

Node nào cần fulltext thì gọi `load_ref()` → kéo từ object store; node
khác chỉ giữ ref.

#### 6.3 Persistence cho cache nóng

Dùng `langgraph.checkpoint.sqlite.SqliteSaver` (đã có trong TradingAgents
qua `graph/checkpointer.py`) để lưu state giữa các lần đối tác submit, để:
- Cache prefix của Anthropic vẫn hiệu lực trong TTL.
- Resume khi crash giữa delta analysis.

#### 6.4 Vector store

```python
from langchain_chroma import Chroma
from langchain_anthropic import AnthropicEmbeddings  # hoặc voyage/openai

fifa_index = Chroma.from_documents(fifa_chunks, embeddings,
                                    collection_name="fifa_v2026")
vendor_index = Chroma.from_documents(vendor_chunks, embeddings,
                                      collection_name="vendor_catalog")
```

Re-index khi: FIFA cập nhật bản mới, vendor cập nhật giá/spec; còn lại
giữ nguyên → embedding cost amortize sau vài tháng.

#### 6.5 Observability bắt buộc

- **LangSmith** hoặc tự log: input/output tokens, cache_read_input_tokens,
  cache_creation_input_tokens cho mỗi node.
- Dashboard "$/dự án" và "$/đối tác" để phát hiện regression khi chỉnh
  prompt.
- Anthropic trả `usage.cache_read_input_tokens` và
  `usage.cache_creation_input_tokens` trong mỗi response — log lại để biết
  cache hit thực sự bao nhiêu %.

### 7. Tóm tắt thiết kế

| Quyết định | Lý do |
|---|---|
| Phân tách `PROJECT_STATE` (cache nóng) ↔ `SOLUTION_DELTA` (transient) | Mỗi đối tác mới chỉ trả "delta cost" |
| Anthropic prompt caching ở 2 breakpoint | Đòn bẩy đơn lẻ tốt nhất, ~70% giảm cost cho debate |
| Hierarchical summary giữa tầng | Cắt context debate 10× |
| RAG cho FIFA/vendor catalog | Bỏ nhồi PDF, giảm hallucination |
| Three-tier model routing | Cân bằng chất lượng / chi phí |
| Map-reduce debate + early stop | Cắt 30-50% token debate |
| Batch API cho sweep | Giảm 50% chi phí re-analysis định kỳ |
| LangGraph state-by-reference | State nhẹ, không bloat snapshot |

Với kiến trúc này, **chi phí biên cho 1 đối tác mới ~$0.6–1.2**, và **chi
phí khởi tạo dự án ~$2-3** thay vì hàng chục USD nếu rerun thuần. Hệ
thống sẵn sàng scale tới hàng trăm giải pháp đối tác trong vòng đời 1 dự
án mà tổng cost vẫn dưới 3 chữ số USD.
