from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import datetime
import math

# -------------------------------------------------------------------------
# 0) Data Contracts
# -------------------------------------------------------------------------

@dataclass
class TickerData:
    symbol: str
    price: float
    high: float
    low: float
    open: float
    close: float
    prevClose: float
    changePct: float
    volume: float
    avgVol20: float
    avgVol50: float
    sma50: float
    sma200: float
    ema9: float
    ema21: float
    rsTrend: str  # "rising" | "flat" | "falling"
    recentHigh20: float
    recentLow20: float
    daysToEarnings: Optional[int] = None
    earningsMoveFlag: bool = False
    gapPctToday: float = 0.0
    gapPctPrevDay: float = 0.0
    candlesDaily: List[dict] = field(default_factory=list)

@dataclass
class OptionsSnapshot:
    hasOptions: bool = False
    spreadPct: float = 0.0
    openInterest: int = 0
    totalVolume: int = 0

@dataclass
class PatternResult:
    name: str = "None"
    confidence: float = 0.0
    pivotPrice: Optional[float] = None
    stage: str = "None" # "Base", "NearPivot", "Breakout"
    notes: str = ""

@dataclass
class SetupDecision:
    accountId: int
    ticker: str
    grade: str
    score: int
    entryPlan: List[str]
    stopPlan: List[str]
    exitPlan: List[str]
    tags: List[str]
    pattern: PatternResult
    reasons: List[str]
    price: float
    changePct: float
    state: str = "WATCH" # "READY", "WATCH"
    setupStage: str = "" # "BO_TODAY", "BASE_BUILDING", etc.


# -------------------------------------------------------------------------
# 1) Global Constants
# -------------------------------------------------------------------------
EARNINGS_DAYS_BLOCK_SHORT = 7
EARNINGS_DAYS_BLOCK_OPTIONS = 10
EXTENDED_FROM_SMA50_WARN = 0.20
EXTENDED_FROM_EMA21_WARN = 0.15
OPT_MIN_GRADE_SCORE = 70
OPT_MAX_SPREAD_PCT = 0.05
OPT_MIN_OI = 1000

# -------------------------------------------------------------------------
# 2) Helper Functions
# -------------------------------------------------------------------------

def is_earnings_noise(td: TickerData) -> bool:
    if td.earningsMoveFlag:
        return True
    if td.daysToEarnings and td.daysToEarnings <= 3 and abs(td.gapPctToday) >= 0.06:
        return True
    if abs(td.gapPctPrevDay) >= 0.08: 
        return True
    return False

def earnings_penalty(td: TickerData) -> int:
    if not is_earnings_noise(td): return 0
    return 12

def trend_score(td: TickerData) -> int:
    s = 0
    if td.price > td.sma50: s += 8 
    else: s -= 8
    
    if td.price > td.sma200: s += 10 
    else: s -= 10
    
    if td.sma50 > td.sma200: s += 10 
    else: s -= 10
    
    if td.ema9 > td.ema21: s += 5
    
    return max(-25, min(25, s))

def rs_score(td: TickerData) -> int:
    if td.rsTrend == "rising": return 12
    if td.rsTrend == "flat": return 4
    return -10

def volume_score(td: TickerData) -> int:
    s = 0
    if td.volume >= 1.5 * td.avgVol20: s += 8
    if td.changePct > 0: s += 7
    else: s -= 5
    return max(-15, min(15, s))

def extended_penalty(td: TickerData) -> int:
    p = 0
    if td.sma50 > 0:
        dist50 = (td.price - td.sma50) / td.sma50
        if dist50 >= EXTENDED_FROM_SMA50_WARN: p += 10
        
    if td.ema21 > 0:
        dist21 = (td.price - td.ema21) / td.ema21
        if dist21 >= EXTENDED_FROM_EMA21_WARN: p += 8
        
    # Climactic action check
    today_range_pct = (td.high - td.low) / td.low if td.low > 0 else 0
    if today_range_pct >= 0.07 and td.volume >= 2.0 * td.avgVol20:
        p += 6
    return p

def detect_pattern(td: TickerData) -> PatternResult:
    pr = PatternResult()
    
    # 1. Breakout detection (Pivot = 20d High)
    pivot = td.recentHigh20
    
    # Check "Near Pivot" (within 3%)
    if pivot > 0 and 0.97 <= td.price / pivot <= 1.02:
        pr.name = "Consolidation"
        pr.stage = "NearPivot"
        pr.confidence = 0.60
        pr.pivotPrice = pivot
        
    # Check "Breakout" (Price > Pivot)
    elif pivot > 0 and td.price > pivot:
        pr.name = "Breakout"
        pr.stage = "Breakout"
        pr.confidence = 0.70
        pr.pivotPrice = pivot
        
    # Check "Base Building" (Below Pivot but above SMA50)
    elif td.price < pivot and td.price > td.sma50:
         pr.name = "Base"
         pr.stage = "Base"
         pr.confidence = 0.50
         pr.pivotPrice = pivot
    
    return pr

def options_liquidity_tag(opt: OptionsSnapshot) -> Tuple[bool, List[str]]:
    tags = []
    if not opt.hasOptions:
        return False, ["NoOptions"]
    
    if opt.spreadPct <= OPT_MAX_SPREAD_PCT: tags.append("TightSpread")
    else: tags.append("WideSpread")
    
    if opt.openInterest >= OPT_MIN_OI: tags.append("GoodOI")
    else: tags.append("LowOI")
    
    good = (opt.spreadPct <= OPT_MAX_SPREAD_PCT) and (opt.openInterest >= OPT_MIN_OI)
    return good, tags

# -------------------------------------------------------------------------
# 3) Scoring Engine
# -------------------------------------------------------------------------

def compute_score(td: TickerData, opt: OptionsSnapshot, pattern: PatternResult) -> Tuple[int, List[str], List[str]]:
    tags = []
    reasons = []
    
    base = 60
    
    t = trend_score(td)
    r = rs_score(td)
    v = volume_score(td)
    
    base += (t + r + v)
    
    # Pattern Score
    if pattern.stage == "Breakout":
        base += 15
        reasons.append("Pattern: Breakout")
    elif pattern.stage == "NearPivot":
        base += 10
        reasons.append("Pattern: Near Pivot (Setting Up)")
    elif pattern.stage == "Base":
        base += 5
        reasons.append("Pattern: Base Building")

    # Penalties
    ep = extended_penalty(td)
    if ep > 0:
        base -= ep
        tags.append("Extended")
        reasons.append(f"Extended penalty: -{ep}")
        
    earnP = earnings_penalty(td)
    if earnP > 0:
        base -= earnP
        tags.append("EarningsNoise")
    
    optGood, optTags = options_liquidity_tag(opt)
    tags.extend(optTags)
    if optGood: tags.append("OptionsOK")
        
    score = max(0, min(100, int(base)))
    reasons.append(f"Trend:{t} RS:{r} Vol:{v}")
    
    return score, tags, reasons

def grade_from_score(score: int) -> str:
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 75: return "B+"
    if score >= 65: return "B"
    if score >= 55: return "C"
    return "D"

# -------------------------------------------------------------------------
# 5) Account Assignmnet (Refined)
# -------------------------------------------------------------------------
def assign_account(td: TickerData, opt: OptionsSnapshot, score: int, tags: List[str], pattern: PatternResult) -> Tuple[int, str, str]:
    """Returns (AccountId, State, SetupStage)"""
    
    state = "WATCH"
    setup_stage = "None"
    
    # -------------------------------------------------
    # Account 3: POS BO/SQ (20-60 days)
    # -------------------------------------------------
    pivot = pattern.pivotPrice if pattern.pivotPrice else td.recentHigh20

    # BO_TODAY
    if pattern.stage == "Breakout" and td.volume >= 1.4 * td.avgVol20 and score >= 70:
        return 3, "READY", "BO_TODAY"
        
    # BO_RECENT (Price > pivot, but maybe vol low today or it was few days ago)
    if pattern.stage == "Breakout" and score >= 65:
        return 3, "WATCH", "BO_RECENT"
        
    # TIGHT_NEAR_PIVOT
    if pattern.stage == "NearPivot" and score >= 65:
        return 3, "WATCH", "NEAR_PIVOT"

    # -------------------------------------------------
    # Account 4: POS HVOL (Pocket Pivot / Accumulation)
    # -------------------------------------------------
    # Simplified: 2x Vol OR recent accumulation
    if score >= 65 and td.volume > 2.0 * td.avgVol20:
        return 4, "READY", "POCKET_PIVOT"
        
    # Accumulation Cluster (Mock: Vol > 1.2x avg)
    if score >= 60 and td.volume > 1.2 * td.avgVol20:
         return 4, "WATCH", "ACCUMULATION"

    # -------------------------------------------------
    # Account 5: POS PAT (Patterns)
    # -------------------------------------------------
    if pattern.stage == "NearPivot" and score >= 65:
        return 5, "WATCH", "HANDLE_FORMING"
        
    if pattern.stage == "Base" and score >= 55: 
        # Lower score accepted for bases, but it's just "WATCH"
        return 5, "WATCH", "BASE_BUILDING"
        
    # -------------------------------------------------
    # Account 6: INV (Long Term)
    # -------------------------------------------------
    # Primary logic: Up Trend
    is_uptrend = td.price > td.sma200 and td.sma50 > td.sma200
    if is_uptrend:
        if "Extended" in tags:
            return 6, "WATCH", "EXTENDED_WAIT"
        elif score >= 60:
            return 6, "READY", "BUYABLE_PULLBACK" if (td.price < td.sma50 * 1.05) else "HOLD/ADD"
            
    # -------------------------------------------------
    # Account 1: Short Swing (Momentum)
    # -------------------------------------------------
    is_short_swing = td.close > td.ema9 and td.close > td.ema21
    if is_short_swing and score >= 70 and pattern.stage == "Breakout":
         return 1, "READY", "MOMENTUM_BREAK"

    # -------------------------------------------------
    # Account 7: OPT Swing
    # -------------------------------------------------
    optGood = "OptionsOK" in tags
    if optGood and score >= 70 and pattern.stage in ["Breakout", "NearPivot"]:
        state = "READY" if pattern.stage == "Breakout" else "WATCH"
        return 7, state, f"OPT_{pattern.stage.upper()}"

    return 0, "WATCH", "NONE"

# -------------------------------------------------------------------------
# 6) Main Interface
# -------------------------------------------------------------------------

def analyze_ticker(td: TickerData, opt: OptionsSnapshot) -> SetupDecision:
    pattern = detect_pattern(td)
    score, tags, reasons = compute_score(td, opt, pattern)
    grade = grade_from_score(score)
    
    account_id, state, setup_stage = assign_account(td, opt, score, tags, pattern)
    
    # Generate plans based on the assigned account, even if it's just WATCH
    entry, stop, exit_p = build_plan(account_id, td, pattern)

    return SetupDecision(
        accountId=account_id,
        ticker=td.symbol,
        grade=grade,
        score=score,
        entryPlan=entry,
        stopPlan=stop,
        exitPlan=exit_p,
        tags=list(set(tags)),
        pattern=pattern,
        reasons=reasons,
        price=td.price,
        changePct=td.changePct,
        state=state,
        setupStage=setup_stage
    )
