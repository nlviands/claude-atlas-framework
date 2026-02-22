# Scanner Playbook: Finding Investment Ideas

*Created: 2026-02-21 | Status: Active — refine as we learn*

---

## Philosophy

Stop paying others to find stocks. Build the skill to find them ourselves using quantitative screens, then layer on qualitative judgment. Two distinct strategies, two distinct scanners.

---

## Scanner 1: Multibagger Finder

### The Research Foundation

**Source:** Anna Yartseva, "The Alchemy of Multibagger Stocks" (Birmingham City University, 2025). Analyzed **464 stocks that returned 10x+** on NYSE/NASDAQ between 2009-2024, testing 150+ variables across 11,600 company-year observations. Covered by Nico at Multibagger Ideas in "The Blueprint for 1,000%+ Returns."

### What 464 Ten-Baggers Looked Like at the Starting Line

| Metric | Median Value |
|--------|-------------|
| Market Cap | $348M |
| Revenue | $702M |
| P/S | 0.6x |
| P/B | 1.1x |
| Forward P/E | 11.3x |
| PEG | 0.8 |
| Gross Margin | 34.8% |
| Operating Margin | 3.9% |
| ROE | 9.0% |

### What They Grew Into (15-year CAGRs)

- Revenue: 11.1%
- Operating Profit: 17.3%
- Net Profit: 22.9%
- EPS: 20.0%

### The Surprise: What Did NOT Predict Performance

Yartseva found **zero predictive power** from: earnings growth rates, EBITDA growth, EPS growth, FCF growth, dividend policies, debt levels, share buybacks, analyst coverage, Altman Z-scores, and R&D spending.

### The Top 10 Metrics That DO Predict Multibaggers

#### 1. Free Cash Flow Yield (THE #1 PREDICTOR)
- **Metric:** FCF / Market Cap
- **Threshold:** >5-6% (top 30% of universe)
- **Why:** Coefficient of 46-82 in regression — 1% higher FCF yield = 46-82% higher annual returns
- **Screen in:** Koyfin, TIKR, Finviz (FCF field)

#### 2. Market Capitalization
- **Threshold:** Under $2B, ideal zone $100M-$500M
- **Why:** Small caps generated 37.7% annual excess returns vs 14.5% for mid-caps and 9.7% for large-caps
- **Screen in:** All screeners

#### 3. Price-to-Book (Value Entry)
- **Threshold:** Under 2.0, ideally 1.0-1.5
- **Why:** High book-to-market = 34.7% annual excess returns vs 12.8% for expensive stocks
- **Screen in:** All screeners

#### 4. Price-to-Sales
- **Threshold:** Under 1.5, ideally 0.5-0.8x
- **Why:** Median was 0.6x. Even modest margin expansion + re-rating = 3-5x before growth
- **Screen in:** All screeners

#### 5. PEG Ratio
- **Threshold:** Under 1.0
- **Why:** Peter Lynch's core signal. Median was 0.8 for the 464 ten-baggers
- **Screen in:** Finviz, Barchart, TOS

#### 6. ROIC (Business Quality Gate)
- **Threshold:** >15%, ideally 20%+
- **Why:** Chris Mayer's hard floor for 100-baggers. Signals durable competitive advantage
- **Screen in:** Finviz (ROI proxy), Koyfin, TIKR (true ROIC)

#### 7. Position in 52-Week Range (Contrarian Entry)
- **Threshold:** Bottom 50% of range (near 12-month lows)
- **Why:** Each 1% closer to 52-week high reduced returns by 0.7-0.9%. Multibaggers start from depressed levels
- **Screen in:** Finviz, Barchart, TOS custom scan

#### 8. Insider/Founder Ownership
- **Threshold:** >10%, ideally 20%+ with active founder/CEO
- **Why:** Every practitioner framework emphasizes this. Aligned incentives compound for decades
- **Screen in:** Finviz (has ownership % filter), Koyfin, OpenInsider.com

#### 9. Asset Growth vs EBITDA Growth (Capital Discipline)
- **Metric:** Asset growth should be LESS than EBITDA growth
- **Why:** Excess asset growth = -4.7% to -22.8% annual return penalty ("empire building" detector)
- **Screen in:** Koyfin (separate fields), manual calculation

#### 10. Gross Margin (Pricing Power)
- **Threshold:** >35-40%
- **Why:** Pricing power, room for operating leverage. Median was 34.8%
- **Screen in:** All screeners

### Composite Screen — Run in Finviz (free)

```
finviz.com/screener.ashx

Market Cap: Micro ($50M-$300M) + Small ($300M-$2B)
P/S: Under 1.5
P/B: Under 2.0
PEG: Under 1.0
ROI: Over 15%
Gross Margin: Over 30%
Insider Ownership: Over 10%
52-Week High/Low: 0-30% above low
```

Then manually check survivors for:
- [ ] FCF yield > 5%
- [ ] Revenue growing > 10% YoY
- [ ] Recurring/subscription revenue model
- [ ] Serial acquirer pattern (rising goodwill on balance sheet)
- [ ] Share dilution < 3%/year
- [ ] Founder/operator still active

### Serial Acquirer Sub-Screen

| Criteria | Threshold |
|----------|-----------|
| Goodwill as % of Assets | Rising over 3-5 years, >20% |
| Revenue CAGR (5yr) | >15% |
| ROIC | >12-15% despite acquisitions |
| FCF Conversion | >70% of EBITDA |
| Insider Ownership | >15% |
| Debt/Equity | <1.5x |

Red flags: goodwill impairments, declining ROIC, dilution >3%/yr, CEO turnover.

### Key Practitioner Frameworks

| Who | Core Logic |
|-----|-----------|
| **Yartseva (Academic)** | Small + cheap (high B/M) + profitable + high FCF yield + near 52-wk low |
| **Chris Mayer (100 Baggers)** | Small cap <$1B + ROIC >15% + owner-operator + low payout + reinvestment runway |
| **Peter Lynch** | PEG <1.0 + EPS growth 15-25% + low debt + manageable P/E |
| **Mohnish Pabrai** | "Spawner DNA" + high ROIC + aggressive reinvestment + >50% discount to intrinsic value |
| **Ian Cassel (MicroCapClub)** | Micro-cap <$500M + profitable + positive FCF + founder-led + <5 analysts |
| **Nico (Multibagger Ideas)** | Serial acquirer OR recurring compounder + fragmented market + founder-owned + cheap EV/EBITDA |

---

## Scanner 2: Rashad-Style Options Income (0-45 DTE)

### Strategy Overview

Sell premium on liquid, elevated-IV stocks with no near-term earnings. Close at 50% profit. Rinse and repeat.

### Step 1 — TOS Stock Hacker (Find Underlying Stocks)

| Filter | Setting |
|--------|---------|
| Stock Price | $20 - $200 |
| Average Volume | > 500,000 |
| Custom Study: IV Rank | > 30 (use thinkScript below) |
| Custom Study: Earnings | No earnings within 30 days |

**IV Rank thinkScript** (Stock Hacker > Add Study > Custom):
```thinkscript
def IV = if isNaN(imp_Volatility()) then IV[1] else imp_Volatility();
def highIV = Highest(IV, 252);
def lowIV = Lowest(IV, 252);
def IVRank = if (highIV - lowIV) > 0 then (IV - lowIV) / (highIV - lowIV) * 100 else 0;
plot scan = IVRank > 30;
```

**Earnings Exclusion thinkScript:**
```thinkscript
plot scan = !HasEarnings(EarningTime.ANY, 0, 30);
```

Save results as watchlist: **"CSP Candidates"**

### Step 2 — TOS Option Hacker (Find Specific Contracts)

| Filter | Setting |
|--------|---------|
| Scan In | "CSP Candidates" watchlist |
| Option Type | Put only |
| DTE | 7 - 45 |
| Delta | -0.35 to -0.15 |
| Open Interest | > 500 |
| Prob of Expiring OTM | > 70% |

Sort by premium. Manually verify tight bid-ask spreads.

### Step 3 — Barchart Alternative (Stronger for Options)

Barchart's Naked Puts screener has built-in:
- IV Rank / IV Percentile filters
- DTE range selector
- Return % and annualized return
- Probability of profit
- Delta and all Greeks
- Strategy-specific screeners (CSPs, CCs, spreads, condors, butterflies)

**Premier feature ($29.95/mo):** Auto-run saved screens and email results before market open.

### Daily Routine

1. Pre-market: Run Stock Hacker scan (or check Barchart email)
2. Review: Pick top 5-10 candidates by IV Rank
3. Verify: No earnings within DTE window (earningswhispers.com)
4. Analyze: TOS Analyze tab — check max loss, breakeven, margin impact
5. Enter: Sell CSP or CC. Set GTC order to close at 50% profit.

### TOS Limitations and Workarounds

| Need | TOS Can Do? | Workaround |
|------|-------------|------------|
| IV Rank | YES | Custom thinkScript (above) |
| Delta filter | YES | Option Hacker built-in |
| DTE range | YES | Option Hacker built-in |
| Open Interest | YES | Option Hacker built-in |
| Prob OTM | YES | Option Hacker built-in |
| Bid-Ask Spread | NO (can't filter) | Add custom column, sort ascending |
| Premium % of Strike | NO | Delta -0.15 to -0.35 with IVR >30 naturally yields 1-3% |
| Earnings exclusion | PARTIAL | HasEarnings() works ~30 days out. Verify manually beyond that |
| Revenue growth | NO | Use Finviz as pre-filter |
| Insider ownership | NO | Use Finviz as pre-filter |
| EV/EBITDA | NO | Use Koyfin or GuruFocus |

---

## Tool Stack

| Tool | Use For | Cost |
|------|---------|------|
| **Finviz** | Multibagger fundamental screening | Free |
| **TOS Stock Hacker** | IV Rank scanning + technical filters | Free (Schwab) |
| **TOS Option Hacker** | Finding specific CSP/CC contracts | Free (Schwab) |
| **Barchart** | Options strategy screener + auto-email alerts | Subscription (have it) |
| **Koyfin** | Advanced fundamentals (ROIC, FCF yield, EV/EBITDA) | Free tier |
| **OpenInsider.com** | Recent insider buying activity | Free |
| **earningswhispers.com** | Earnings date verification | Free |

---

## Sources & Further Reading

### Academic Research
- Yartseva, "The Alchemy of Multibagger Stocks" (CAFE Working Paper No. 33, 2025) — [PDF](https://www.open-access.bcu.ac.uk/16180/1/The%20Alchemy%20of%20Multibagger%20Stocks%20-%20Anna%20Yartseva%20-%20CAFE%20Working%20Paper%2033%20(2025).pdf)
- StableBread summary: [What 464 10-Baggers Reveal](https://stablebread.com/464-10-baggers-research/)

### Practitioner
- Chris Mayer, *100 Baggers* — [Compounding Quality summary](https://www.compoundingquality.net/p/a-guide-to-finding-100-baggers)
- 100baggerhunting.com — [Investment Checklist](https://www.100baggerhunting.com/p/how-to-hunt-for-100-baggers-an-investment)
- Multibagger Ideas (Nico) — [Complete Guide to Finding Multibaggers](https://multibaggerideas.substack.com/p/your-complete-guide-to-finding-multibaggers)
- Multibagger Ideas — [100+ Serial Acquirers from Around the World](https://multibaggerideas.substack.com/p/100-serial-acquirers-from-around)
- Exploring Context — [Studying Serial Acquirers](https://exploringcontext.substack.com/p/studying-serial-acquirers)
- Pabrai's Spawner Framework — [Sven Carlin summary](https://svencarlin.com/mohnish-pabrai-spawner-investing-framework/)

### Tools
- [Finviz Screener](https://finviz.com/screener.ashx)
- [Barchart Options Screener](https://www.barchart.com/options/options-screener)
- [TOS Stock Hacker Docs](https://toslc.thinkorswim.com/center/howToTos/thinkManual/Scan/Stock-Hacker)
- [TOS Option Hacker Docs](https://toslc.thinkorswim.com/center/howToTos/thinkManual/Scan/Option-Hacker)
- [useThinkScript: IV Rank](https://usethinkscript.com/threads/implied-volatility-iv-rank-percentile-for-thinkorswim.674/)

---

## Improvement Log

Track what works and what doesn't as we refine the screens.

| Date | Change | Result |
|------|--------|--------|
| 2026-02-21 | Initial playbook created | Baseline |
| | | |
