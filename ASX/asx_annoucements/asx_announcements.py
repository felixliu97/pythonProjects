"""
ASX Price Sensitive Announcement Scanner

Scans ASX for today's price-sensitive announcements and analyzes stocks
for potential upward trends while filtering out "sell on news" scenarios.

Usage:
    python asx_announcements.py

Requirements:
    pip install playwright yfinance pandas numpy pdfplumber requests
    playwright install chromium
"""

import asyncio
import io
import json
import os
import re
import time
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import logging
import io
import sys

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from playwright.async_api import async_playwright

# Suppress yfinance verbose error messages
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# PDF handling - optional import
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Warning: pdfplumber not installed. PDF analysis disabled. Install with: pip install pdfplumber")

warnings.filterwarnings('ignore')


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class Announcement:
    """Represents a single ASX announcement"""
    asx_code: str
    company_name: str
    headline: str
    date_time: str
    is_price_sensitive: bool
    pdf_link: str = ""
    pages: int = 0
    file_size: str = ""
    pdf_content: str = ""  # Extracted text from PDF
    pdf_analysis: Dict = field(default_factory=dict)  # Analysis results from PDF


@dataclass
class StockAnalysis:
    """Technical analysis results for a stock"""
    symbol: str
    current_price: float = 0.0
    rsi: float = 50.0
    volume_ratio: float = 1.0  # current volume / avg volume
    price_change_5d: float = 0.0
    price_change_today: float = 0.0
    volatility: float = 0.0
    is_golden_cross: bool = False  # SMA 50 > SMA 200
    
    
@dataclass  
class ScanResult:
    """Combined announcement and analysis result"""
    announcement: Announcement
    analysis: Optional[StockAnalysis] = None
    buy_score: float = 0.0
    sell_on_news_score: float = 0.0
    classification: str = "NEUTRAL"  # BUY, NEUTRAL, SELL
    reasons: List[str] = field(default_factory=list)
    summary: str = ""  # Short summary of the announcement


# ============================================================================
# Colors for Console Output
# ============================================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


# ============================================================================
# ASX Announcement Scraper
# ============================================================================


class ASXAnnouncementScraper:
    """Scrapes price-sensitive announcements from ASX website using Playwright"""
    
    # Direct URL to the announcements iframe content
    ASX_IFRAME_URL = "https://www.asx.com.au/asx/v2/statistics/todayAnns.do"
    
    async def scrape_announcements(self, price_sensitive_only: bool = True, headless: bool = True) -> List[Announcement]:
        """Fetch today's announcements from ASX website"""
        announcements = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless, slow_mo=50)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()
            
            try:
                print(f"{Colors.CYAN}Loading ASX announcements...{Colors.ENDC}")
                
                # Go directly to the iframe URL for faster loading
                await page.goto(self.ASX_IFRAME_URL, timeout=60000, wait_until="domcontentloaded")
                
                # Wait for table to load
                await asyncio.sleep(3)
                
                # Extract announcements using the correct table structure
                data = await page.evaluate("""
                    () => {
                        const results = [];
                        const rows = document.querySelectorAll('table tr');
                        
                        for (const row of rows) {
                            const cells = row.querySelectorAll('td');
                            if (cells.length < 4) continue;
                            
                            // Column 0: ASX Code
                            const codeText = cells[0]?.innerText?.trim() || '';
                            if (!/^[A-Z0-9]{2,4}$/.test(codeText)) continue;
                            
                            // Column 1: Date/Time (date text + span.dates-time for time)
                            const dateCell = cells[1];
                            const dateText = dateCell?.childNodes[0]?.textContent?.trim() || '';
                            const timeSpan = dateCell?.querySelector('.dates-time');
                            const timeText = timeSpan?.innerText?.trim() || '';
                            const dateTime = `${dateText} ${timeText}`.trim();
                            
                            // Column 2: Price Sensitivity - look for img.pricesens
                            const priceSensCell = cells[2];
                            const priceSensImg = priceSensCell?.querySelector('img.pricesens');
                            const isPriceSensitive = priceSensImg !== null;
                            
                            // Column 3: Headline and PDF link
                            const headlineCell = cells[3];
                            const link = headlineCell?.querySelector('a');
                            const headline = link?.innerText?.split('\\n')[0]?.trim() || '';
                            let pdfLink = link?.href || '';
                            
                            // Make PDF link absolute if relative
                            if (pdfLink && !pdfLink.startsWith('http')) {
                                pdfLink = 'https://www.asx.com.au' + pdfLink;
                            }
                            
                            // Get page count and file size from spans
                            const pageSpan = headlineCell?.querySelector('.page');
                            const sizeSpan = headlineCell?.querySelector('.filesize');
                            const pages = parseInt(pageSpan?.innerText) || 0;
                            const fileSize = sizeSpan?.innerText?.trim() || '';
                            
                            if (headline && codeText) {
                                results.push({
                                    asx_code: codeText,
                                    date_time: dateTime,
                                    is_price_sensitive: isPriceSensitive,
                                    headline: headline,
                                    pdf_link: pdfLink,
                                    pages: pages,
                                    file_size: fileSize
                                });
                            }
                        }
                        
                        return { 
                            data: results, 
                            total_rows: rows.length 
                        };
                    }
                """)
                
                total_rows = data.get('total_rows', 0)
                items = data.get('data', [])
                print(f"{Colors.CYAN}Found {total_rows} rows, extracted {len(items)} announcements{Colors.ENDC}")
                
                for item in items:
                    is_price_sensitive = item.get('is_price_sensitive', False)
                    headline = item.get('headline', '')
                    
                    # Filter by price sensitivity if requested
                    if price_sensitive_only and not is_price_sensitive:
                        continue
                    
                    # Exclude Trading Halt announcements
                    if 'trading halt' in headline.lower():
                        continue
                        
                    ann = Announcement(
                        asx_code=item['asx_code'],
                        company_name=item['asx_code'],
                        headline=item.get('headline', ''),
                        date_time=item.get('date_time', ''),
                        is_price_sensitive=is_price_sensitive,
                        pdf_link=item.get('pdf_link', ''),
                        pages=item.get('pages', 0),
                        file_size=item.get('file_size', '')
                    )
                    announcements.append(ann)
                    
            except Exception as e:
                print(f"{Colors.FAIL}Error scraping announcements: {e}{Colors.ENDC}")
                import traceback
                traceback.print_exc()
            finally:
                await browser.close()
        
        if len(announcements) == 0:
            print(f"\n{Colors.WARNING}No price-sensitive announcements found.{Colors.ENDC}")
            print(f"{Colors.WARNING}Try running with --all flag to see all announcements.{Colors.ENDC}")
        
        print(f"{Colors.GREEN}Found {len(announcements)} price-sensitive announcements{Colors.ENDC}")
        return announcements


# ============================================================================
# PDF Analyzer
# ============================================================================

class PDFAnalyzer:
    """Downloads and analyzes PDF announcement content"""
    
    # Buy signal patterns with scores
    BUY_PATTERNS = [
        (r'high[\s-]*grade', 20, 'High grade results'),
        (r'significant\s+intercept', 15, 'Significant intercept'),
        (r'metres?\s+@\s+[\d.]+\s*g/t', 15, 'Gold assay results'),
        (r'metres?\s+@\s+[\d.]+\s*%', 15, 'Base metal assay results'),
        (r'contract\s+(?:awarded|signed|won)', 20, 'Contract awarded'),
        (r'\$[\d,]+\s*(?:million|m)\s+contract', 20, 'Major contract value'),
        (r'acquisition\s+(?:of|complete)', 15, 'Acquisition'),
        (r'fda\s+approval', 25, 'FDA approval'),
        (r'tga\s+approval', 20, 'TGA approval'),
        (r'patent\s+(?:granted|approved)', 15, 'Patent granted'),
        (r'partnership\s+(?:with|agreement)', 10, 'Partnership'),
        (r'binding\s+(?:agreement|mou)', 15, 'Binding agreement'),
        (r'maiden\s+resource', 20, 'Maiden resource'),
        (r'resource\s+upgrade', 15, 'Resource upgrade'),
        (r'production\s+(?:commenced|started)', 15, 'Production started'),
        (r'exceeds?\s+guidance', 15, 'Exceeds guidance'),
        (r'record\s+(?:revenue|profit|production)', 10, 'Record results'),
        (r'profit\s+(?:up|increased|grew)', 10, 'Profit growth'),
        (r'revenue\s+(?:up|increased|grew)', 10, 'Revenue growth'),
        (r'(?:new|renewed)\s+(?:order|contract)', 15, 'New order'),
    ]
    
    # Sell/caution signal patterns with scores
    SELL_PATTERNS = [
        (r'capital\s+raising?', 20, 'Capital raise'),
        (r'placement\s+(?:at|to)\s+\$', 20, 'Placement'),
        (r'(?:share|equity)\s+purchase\s+plan', 15, 'SPP/equity raise'),
        (r'rights\s+issue', 15, 'Rights issue'),
        (r'(?:non-renounceable|renounceable)\s+(?:offer|issue)', 15, 'Rights offer'),
        (r'entitlement\s+offer', 15, 'Entitlement offer'),
        (r'discount\s+(?:of|to)\s+[\d.]+%', 15, 'Discounted placement'),
        (r'loss\s+(?:of|for|after)', 15, 'Loss reported'),
        (r'impairment', 15, 'Impairment'),
        (r'write[\s-]*down', 15, 'Write-down'),
        (r'suspended\s+(?:from|trading)', 25, 'Trading suspended'),
        (r'administration|liquidat', 25, 'Administration/liquidation'),
        (r'resignat(?:ion|ed)', 10, 'Resignation'),
        (r'delayed|postponed', 10, 'Delay'),
        (r'guidance\s+(?:reduced|lowered|cut)', 15, 'Guidance cut'),
        (r'profit\s+(?:warning|downgrade)', 20, 'Profit warning'),
        (r'disappointing', 10, 'Disappointing results'),
        (r'below\s+(?:expectations?|guidance)', 15, 'Below expectations'),
    ]
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.pdf_cache_root = os.path.join(os.path.dirname(__file__), '.pdf_cache')
        # Use today's date as subdirectory
        today = datetime.now().strftime('%Y-%m-%d')
        self.pdf_cache_dir = os.path.join(self.pdf_cache_root, today)
        os.makedirs(self.pdf_cache_dir, exist_ok=True)
    
    def download_pdf(self, url: str, asx_code: str = "") -> Optional[bytes]:
        """Download PDF from URL - checks cache first"""
        if not url:
            return None
            
        try:
            # Check cache first - look for {asx_code}_*.pdf in today's folder
            if asx_code:
                for cached_file in os.listdir(self.pdf_cache_dir):
                    if cached_file.startswith(f"{asx_code}_") and cached_file.endswith('.pdf'):
                        cache_path = os.path.join(self.pdf_cache_dir, cached_file)
                        with open(cache_path, 'rb') as f:
                            content = f.read()
                            if content[:4] == b'%PDF':
                                return content
            
            # Not in cache - download
            ids_match = re.search(r'idsId[=_](\d+)', url)
            ids_id = ids_match.group(1) if ids_match else None
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check if response is already a PDF
            if response.content[:4] == b'%PDF':
                pdf_content = response.content
                original_filename = ids_id if ids_id else "unknown"
            else:
                # ASX returns HTML page with the actual PDF URL embedded
                pdf_url_match = re.search(r'https://announcements\.asx\.com\.au[^"\s\']+\.pdf', response.text)
                if not pdf_url_match:
                    return None
                
                # Download the actual PDF
                actual_pdf_url = pdf_url_match.group(0)
                pdf_response = self.session.get(actual_pdf_url, timeout=30)
                pdf_response.raise_for_status()
                
                if pdf_response.content[:4] != b'%PDF':
                    return None
                    
                pdf_content = pdf_response.content
                original_filename = actual_pdf_url.split('/')[-1].replace('.pdf', '')
            
            # Cache the PDF: .pdf_cache/{date}/{ASX_code}_{original_filename}.pdf
            cache_filename = f"{asx_code}_{original_filename}.pdf" if asx_code else f"{original_filename}.pdf"
            cache_file = os.path.join(self.pdf_cache_dir, cache_filename)
            
            with open(cache_file, 'wb') as f:
                f.write(pdf_content)
            
            return pdf_content
        except Exception:
            return None
    
    def extract_text(self, pdf_bytes: bytes, max_pages: int = 5) -> str:
        """Extract text from PDF bytes"""
        if not PDF_SUPPORT or not pdf_bytes:
            return ""
        
        try:
            text_parts = []
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                # Only read first N pages for efficiency
                for i, page in enumerate(pdf.pages[:max_pages]):
                    text = page.extract_text() or ""
                    text_parts.append(text)
            
            return "\n".join(text_parts)
        except Exception:
            # Silently fail - PDF text extraction is optional
            return ""
    
    def analyze_content(self, text: str) -> Dict:
        """Analyze PDF text content for buy/sell signals"""
        if not text:
            return {'buy_score': 0, 'sell_score': 0, 'signals': [], 'document_type': 'unknown'}
        
        text_lower = text.lower()
        buy_score = 0
        sell_score = 0
        signals = []
        
        # Check buy patterns
        for pattern, score, description in self.BUY_PATTERNS:
            if re.search(pattern, text_lower):
                buy_score += score
                signals.append(f"📈 {description}")
        
        # Check sell patterns
        for pattern, score, description in self.SELL_PATTERNS:
            if re.search(pattern, text_lower):
                sell_score += score
                signals.append(f"📉 {description}")
        
        # Extract key numbers (percentages, dollar amounts)
        percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', text)
        large_positive_pcts = [float(p) for p in percentages if float(p) > 20 and float(p) < 1000]
        if large_positive_pcts:
            buy_score += min(len(large_positive_pcts) * 3, 15)
            signals.append(f"📊 Large percentages found: {len(large_positive_pcts)}")
        
        # Detect document type
        doc_type = self._detect_document_type(text_lower)
        
        return {
            'buy_score': min(buy_score, 100),
            'sell_score': min(sell_score, 100),
            'signals': signals[:5],  # Limit to top 5 signals
            'document_type': doc_type,
            'word_count': len(text.split())
        }
    
    def _detect_document_type(self, text: str) -> str:
        """Detect the type of announcement document"""
        if 'drilling' in text or 'assay' in text or 'intercept' in text:
            return 'exploration'
        elif 'quarterly' in text and ('report' in text or 'activities' in text):
            return 'quarterly'
        elif 'half' in text and 'year' in text:
            return 'half_year'
        elif 'annual' in text and 'report' in text:
            return 'annual'
        elif 'capital' in text and 'rais' in text:
            return 'capital_raise'
        elif 'contract' in text or 'agreement' in text:
            return 'contract'
        elif 'acquisition' in text or 'merger' in text:
            return 'mna'
        elif 'trading' in text and 'halt' in text:
            return 'trading_halt'
        else:
            return 'other'
    
    def analyze_announcement(self, announcement: Announcement) -> Announcement:
        """Download and analyze a single announcement's PDF"""
        if not PDF_SUPPORT:
            return announcement
        
        if not announcement.pdf_link:
            return announcement
        
        print(f"  Analyzing PDF for {announcement.asx_code}...", end='\r')
        
        # Download PDF
        pdf_bytes = self.download_pdf(announcement.pdf_link, announcement.asx_code)
        if not pdf_bytes:
            return announcement
        
        # Extract text
        text = self.extract_text(pdf_bytes)
        announcement.pdf_content = text[:5000]  # Store first 5000 chars
        
        # Analyze content
        analysis = self.analyze_content(text)
        announcement.pdf_analysis = analysis
        
        return announcement
    
    def analyze_announcements(self, announcements: List[Announcement], max_workers: int = 10) -> List[Announcement]:
        """Analyze multiple announcements in parallel"""
        if not PDF_SUPPORT:
            print(f"{Colors.WARNING}PDF analysis disabled - pdfplumber not installed{Colors.ENDC}")
            return announcements
        
        print(f"\n{Colors.CYAN}Downloading and analyzing PDFs (parallel)...{Colors.ENDC}")
        
        total = len(announcements)
        completed = [0]  # Use list for mutable counter in closure
        signals_found = [0]
        
        def process_announcement(ann: Announcement) -> Announcement:
            self.analyze_announcement(ann)
            completed[0] += 1
            if ann.pdf_analysis.get('signals'):
                signals_found[0] += 1
            # Progress update
            print(f"\r  [{completed[0]}/{total}] Processed {ann.asx_code}... {signals_found[0]} with signals", end='', flush=True)
            return ann
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            list(executor.map(process_announcement, announcements))
        
        print(f"\n{Colors.GREEN}PDF analysis complete - {signals_found[0]} announcements with signals{Colors.ENDC}")
        return announcements


# ============================================================================
# Stock Analyzer
# ============================================================================

class StockTrendAnalyzer:
    """Analyzes stock technical indicators using Yahoo Finance"""
    
    def __init__(self, config: dict):
        self.config = config.get('analysis', {})
        self.rsi_overbought = self.config.get('rsi_overbought', 70)
        self.rsi_oversold = self.config.get('rsi_oversold', 30)
        self.volume_spike_threshold = self.config.get('volume_spike_threshold', 2.0)
        self.lookback_days = self.config.get('lookback_days', 20)
    
    def get_stock_data(self, symbol: str, period: str = "3mo") -> pd.DataFrame:
        """Fetch stock data with retry logic - suppresses yfinance errors"""
        asx_symbol = f"{symbol}.AX" if not symbol.endswith('.AX') else symbol
        
        for attempt in range(3):
            try:
                # Suppress yfinance stderr output
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()
                try:
                    stock = yf.Ticker(asx_symbol)
                    data = stock.history(period=period)
                finally:
                    sys.stderr = old_stderr
                
                if not data.empty:
                    return data
            except Exception:
                if attempt < 2:
                    time.sleep(0.5 * (2 ** attempt))
        
        return pd.DataFrame()
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0
            
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50.0
    
    def analyze_stock(self, symbol: str) -> Optional[StockAnalysis]:
        """Perform technical analysis on a stock"""
        data = self.get_stock_data(symbol)
        
        if data.empty or len(data) < 10:
            return None
        
        try:
            current_price = float(data['Close'].iloc[-1])
            
            # Calculate today's price change
            price_today = 0.0
            if len(data) >= 2:
                prev_close = float(data['Close'].iloc[-2])
                price_today = ((current_price - prev_close) / prev_close) * 100
            
            # Calculate 5-day price change
            price_5d = 0.0
            if len(data) > 5:
                price_5d = ((current_price - data['Close'].iloc[-6]) / data['Close'].iloc[-6]) * 100
            
            # Volume analysis
            avg_volume = data['Volume'].tail(20).mean()
            current_volume = data['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # RSI
            rsi = self.calculate_rsi(data['Close'])
            
            # Volatility
            returns = data['Close'].pct_change()
            volatility = float(returns.std() * np.sqrt(252) * 100)
            
            # Golden Cross detection (SMA 50 > SMA 200)
            is_golden_cross = False
            if len(data) >= 200:
                sma_50 = data['Close'].tail(50).mean()
                sma_200 = data['Close'].tail(200).mean()
                is_golden_cross = sma_50 > sma_200
            
            return StockAnalysis(
                symbol=symbol,
                current_price=round(current_price, 3),
                rsi=round(rsi, 2),
                volume_ratio=round(volume_ratio, 2),
                price_change_5d=round(price_5d, 2),
                price_change_today=round(price_today, 2),
                volatility=round(volatility, 2),
                is_golden_cross=is_golden_cross
            )
            
        except Exception as e:
            print(f"  Error analyzing {symbol}: {e}")
            return None


# ============================================================================
# Sell-on-News Detector
# ============================================================================

class SellOnNewsDetector:
    """Detects potential 'sell on news' scenarios"""
    
    def __init__(self, config: dict):
        self.sell_keywords = config.get('sell_on_news_keywords', [])
        self.buy_keywords = config.get('buy_signal_keywords', [])
        self.analysis_config = config.get('analysis', {})
        self.runup_threshold = self.analysis_config.get('pre_announcement_runup_threshold', 15.0)
    
    def calculate_sell_on_news_score(self, result: ScanResult) -> tuple:
        """
        Calculate sell-on-news probability score (0-100)
        Returns (score, list of reasons)
        """
        score = 0.0
        reasons = []
        
        ann = result.announcement
        analysis = result.analysis
        
        if not analysis:
            return 0.0, ["No analysis data available"]
        
        headline_lower = ann.headline.lower()
        
        # 1. Check for sell-on-news keywords in headline
        for keyword in self.sell_keywords:
            if keyword.lower() in headline_lower:
                score += 15
                reasons.append(f"Headline contains '{keyword}'")
                break
        
        # 2. High RSI (overbought before announcement)
        if analysis.rsi >= 70:
            score += 25
            reasons.append(f"RSI overbought ({analysis.rsi:.1f})")
        elif analysis.rsi >= 60:
            score += 10
            reasons.append(f"RSI elevated ({analysis.rsi:.1f})")
        
        # 3. Pre-announcement price run-up
        if analysis.price_change_5d >= self.runup_threshold:
            score += 25
            reasons.append(f"Pre-announcement run-up ({analysis.price_change_5d:+.1f}% in 5 days)")
        elif analysis.price_change_5d >= 10:
            score += 15
            reasons.append(f"Recent price increase ({analysis.price_change_5d:+.1f}% in 5 days)")
        
        # 4. Volume exhaustion (very high volume spike may indicate climax)
        if analysis.volume_ratio >= 5.0:
            score += 20
            reasons.append(f"Extreme volume spike ({analysis.volume_ratio:.1f}x average)")
        elif analysis.volume_ratio >= 3.0:
            score += 10
            reasons.append(f"High volume ({analysis.volume_ratio:.1f}x average)")
        
        # 5. High volatility suggests uncertainty
        if analysis.volatility >= 60:
            score += 10
            reasons.append(f"High volatility ({analysis.volatility:.1f}%)")
        
        return min(score, 100), reasons
    
    def calculate_buy_score(self, result: ScanResult) -> tuple:
        """
        Calculate buy potential score (0-100)
        Returns (score, list of reasons)
        """
        score = 0.0
        reasons = []
        
        ann = result.announcement
        analysis = result.analysis
        
        if not analysis:
            return 0.0, ["No analysis data available"]
        
        headline_lower = ann.headline.lower()
        
        # 1. Check for positive keywords
        for keyword in self.buy_keywords:
            if keyword.lower() in headline_lower:
                score += 15
                reasons.append(f"Positive: '{keyword}'")
                break
        
        # 2. RSI not overbought (room to grow)
        if analysis.rsi <= 40:
            score += 20
            reasons.append(f"RSI low ({analysis.rsi:.1f}) - room to grow")
        elif analysis.rsi <= 55:
            score += 10
            reasons.append(f"RSI neutral ({analysis.rsi:.1f})")
        
        # 3. Not already pumped (consolidation breakout potential)
        if -5 <= analysis.price_change_5d <= 5:
            score += 15
            reasons.append("Price consolidated (breakout potential)")
        elif analysis.price_change_5d > 0:
            score += 10
            reasons.append(f"Positive trend ({analysis.price_change_5d:+.1f}%)")
        
        # 4. Reasonable volume (not exhausted)
        if 1.5 <= analysis.volume_ratio <= 3.0:
            score += 15
            reasons.append(f"Healthy volume increase ({analysis.volume_ratio:.1f}x)")
        elif analysis.volume_ratio < 1.5:
            score += 10
            reasons.append("Volume not yet spiked (early discovery)")
        
        # 5. Golden Cross (bullish trend)
        if analysis.is_golden_cross:
            score += 15
            reasons.append("Golden cross (SMA 50 > SMA 200)")
        
        return min(score, 100), reasons


# ============================================================================
# Report Generator
# ============================================================================

class ReportGenerator:
    """Generates console and HTML reports"""
    
    def classify_result(self, result: ScanResult) -> str:
        """Classify stock based on whether positive or negative signals dominate"""
        buy = result.buy_score
        sell = result.sell_on_news_score
        
        # SELL: Negative signals dominate
        if sell >= 25 and sell > buy:
            return "SELL"
        # BUY: Positive signals dominate (lowered threshold)
        elif buy > sell and buy >= 20:
            return "BUY"
        # NEUTRAL: Mixed or unclear signals
        else:
            return "NEUTRAL"
    
    def display_console_report(self, results: List[ScanResult]):
        """Print results to console"""
        if not results:
            print(f"{Colors.WARNING}No announcements to display{Colors.ENDC}")
            return
        
        # Sort by classification priority
        priority = {"BUY": 0, "NEUTRAL": 1, "SELL": 2}
        results.sort(key=lambda x: (priority.get(x.classification, 1), -x.buy_score))
        
        print("\n" + "=" * 100)
        print(f"{Colors.BOLD}ASX PRICE SENSITIVE ANNOUNCEMENTS ANALYSIS{Colors.ENDC}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        
        # Group by classification
        buy_results = [r for r in results if r.classification == "BUY"]
        neutral_results = [r for r in results if r.classification == "NEUTRAL"]
        sell_results = [r for r in results if r.classification == "SELL"]
        
        # Display BUY section
        if buy_results:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🟢 POTENTIAL BUY ({len(buy_results)} stocks){Colors.ENDC}")
            print("-" * 100)
            self._display_section(buy_results)
        
        # Display NEUTRAL section
        if neutral_results:
            print(f"\n{Colors.WARNING}{Colors.BOLD}🟡 NEUTRAL ({len(neutral_results)} stocks){Colors.ENDC}")
            print("-" * 100)
            self._display_section(neutral_results)
        
        # Display SELL section
        if sell_results:
            print(f"\n{Colors.FAIL}{Colors.BOLD}🔴 SELL ({len(sell_results)} stocks){Colors.ENDC}")
            print("-" * 100)
            self._display_section(sell_results)
        
        print("\n" + "=" * 100)
        print(f"Total analyzed: {len(results)} announcements")
        print("=" * 100)
    
    def _display_section(self, results: List[ScanResult]):
        """Display a section of results with ratings and summaries"""
        for r in results:
            ann = r.announcement
            analysis = r.analysis
            
            # Header line
            price_str = f"${analysis.current_price:.3f}" if analysis else "N/A"
            rsi_str = f"{analysis.rsi:.1f}" if analysis else "N/A"
            
            print(f"\n{Colors.BOLD}{ann.asx_code}{Colors.ENDC} | {price_str} | RSI: {rsi_str}")
            print(f"  Headline: {ann.headline[:80]}{'...' if len(ann.headline) > 80 else ''}")
            print(f"  Time: {ann.date_time}")
            
            # Rating and summary (Step 5 output)
            rating_colors = {'BUY': Colors.GREEN, 'WATCH': Colors.WARNING, 'SELL_ON_NEWS': Colors.FAIL}
            rating_color = rating_colors.get(r.classification, Colors.WARNING)
            print(f"  Rating: {rating_color}{r.classification}{Colors.ENDC}")
            print(f"  Summary: {r.summary}")
            
            if analysis:
                today_color = Colors.GREEN if analysis.price_change_today > 0 else Colors.FAIL if analysis.price_change_today < 0 else Colors.WARNING
                chg_color = Colors.GREEN if analysis.price_change_5d > 0 else Colors.FAIL if analysis.price_change_5d < 0 else Colors.WARNING
                print(f"  Technical: {today_color}{analysis.price_change_today:+.2f}%{Colors.ENDC} (Today) | "
                      f"{chg_color}{analysis.price_change_5d:+.2f}%{Colors.ENDC} (5D) | "
                      f"Volume: {analysis.volume_ratio:.1f}x avg")
    
    def generate_html_report(self, results: List[ScanResult], filename: str = None):
        """Generate HTML report"""
        if filename is None:
            filename = f"asx_announcements_{datetime.now().strftime('%Y-%m-%d')}.html"
        
        # Sort results
        priority = {"BUY": 0, "WATCH": 1, "SELL_ON_NEWS": 2}
        results.sort(key=lambda x: (priority.get(x.classification, 1), -x.buy_score))
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>ASX Announcements Analysis</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
               background: #1a1a1a; color: #e0e0e0; margin: 0; padding: 20px; }}
        .header {{ background: #2d2d2d; padding: 20px; border-radius: 8px; margin-bottom: 20px; 
                   border-left: 5px solid #007acc; }}
        h1 {{ margin: 0; color: #007acc; }}
        .timestamp {{ color: #888; font-size: 0.9em; margin-top: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; background: #252526; border-radius: 8px; }}
        .section-title {{ font-size: 1.3em; font-weight: bold; margin-bottom: 15px; }}
        .buy {{ border-left: 4px solid #4caf50; }}
        .buy .section-title {{ color: #4caf50; }}
        .watch {{ border-left: 4px solid #ff9800; }}
        .watch .section-title {{ color: #ff9800; }}
        .sell {{ border-left: 4px solid #f44336; }}
        .sell .section-title {{ color: #f44336; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #333; }}
        th {{ background: #333; color: #fff; cursor: pointer; user-select: none; }}
        th:hover {{ background: #444; }}
        th.sorted-asc::after {{ content: ' ▲'; font-size: 0.8em; }}
        th.sorted-desc::after {{ content: ' ▼'; font-size: 0.8em; }}
        tr:hover {{ background: #2d2d2d; }}
        .positive {{ color: #4caf50; }}
        .negative {{ color: #f44336; }}
        .neutral {{ color: #888; }}
        .score {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: bold; }}
        .score-high {{ background: #4caf50; color: #fff; }}
        .score-med {{ background: #ff9800; color: #fff; }}
        .score-low {{ background: #f44336; color: #fff; }}
        .reasons {{ font-size: 0.85em; color: #aaa; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔔 ASX Announcements Analysis</h1>
        <div class="timestamp">Generated: {timestamp}</div>
    </div>
    
    <script>
    function sortTable(table, colIndex) {{
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const th = table.querySelectorAll('th')[colIndex];
        const isAsc = th.classList.contains('sorted-asc');
        
        // Clear all sort indicators
        table.querySelectorAll('th').forEach(h => h.classList.remove('sorted-asc', 'sorted-desc'));
        
        rows.sort((a, b) => {{
            let aVal = a.cells[colIndex].textContent.trim();
            let bVal = b.cells[colIndex].textContent.trim();
            
            // Handle numeric values (prices, percentages)
            const aNum = parseFloat(aVal.replace(/[$%,+]/g, ''));
            const bNum = parseFloat(bVal.replace(/[$%,+]/g, ''));
            
            if (!isNaN(aNum) && !isNaN(bNum)) {{
                return isAsc ? bNum - aNum : aNum - bNum;
            }}
            
            // String comparison
            return isAsc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
        }});
        
        th.classList.add(isAsc ? 'sorted-desc' : 'sorted-asc');
        rows.forEach(row => tbody.appendChild(row));
    }}
    
    document.addEventListener('DOMContentLoaded', () => {{
        document.querySelectorAll('table').forEach(table => {{
            table.querySelectorAll('th').forEach((th, index) => {{
                th.addEventListener('click', () => sortTable(table, index));
            }});
        }});
    }});
    </script>
"""
        
        # Group by classification
        buy_results = [r for r in results if r.classification == "BUY"]
        neutral_results = [r for r in results if r.classification == "NEUTRAL"]
        sell_results = [r for r in results if r.classification == "SELL"]
        
        def generate_table(results_list, section_class, title, emoji):
            if not results_list:
                return ""
            
            section_html = f"""
    <div class="section {section_class}">
        <div class="section-title">{emoji} {title} ({len(results_list)})</div>
        <table>
            <thead>
                <tr>
                    <th>Code</th>
                    <th>Headline</th>
                    <th>Rating</th>
                    <th>Summary</th>
                    <th>Price</th>
                    <th>Today</th>
                    <th>5D Chg</th>
                </tr>
            </thead>
            <tbody>
"""
            for r in results_list:
                ann = r.announcement
                a = r.analysis
                
                price = f"${a.current_price:.3f}" if a else "-"
                chg_today = f"{a.price_change_today:+.1f}%" if a else "-"
                chg_5d = f"{a.price_change_5d:+.1f}%" if a else "-"
                today_class = "positive" if a and a.price_change_today > 0 else "negative" if a and a.price_change_today < 0 else "neutral"
                chg_class = "positive" if a and a.price_change_5d > 0 else "negative" if a and a.price_change_5d < 0 else "neutral"
                
                rating_class = "score-high" if r.classification == "BUY" else "score-low" if r.classification == "SELL" else "score-med"
                
                section_html += f"""
                <tr>
                    <td><strong>{ann.asx_code}</strong></td>
                    <td>{ann.headline[:60]}{'...' if len(ann.headline) > 60 else ''}</td>
                    <td><span class="score {rating_class}">{r.classification}</span></td>
                    <td>{r.summary}</td>
                    <td>{price}</td>
                    <td class="{today_class}">{chg_today}</td>
                    <td class="{chg_class}">{chg_5d}</td>
                </tr>
"""
            
            section_html += """
            </tbody>
        </table>
    </div>
"""
            return section_html
        
        html += generate_table(buy_results, "buy", "POTENTIAL BUY", "🟢")
        html += generate_table(neutral_results, "watch", "NEUTRAL", "🟡")
        html += generate_table(sell_results, "sell", "SELL", "🔴")
        
        html += f"""
    <div class="section">
        <p>Total analyzed: <strong>{len(results)}</strong> price-sensitive announcements</p>
        <p style="color: #666; font-size: 0.9em;">💡 Click any column header to sort</p>
    </div>
</body>
</html>
"""
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n{Colors.GREEN}HTML report saved: {filepath}{Colors.ENDC}")
        return filepath


# ============================================================================
# Main Scanner
# ============================================================================

class ASXAnnouncementScanner:
    """Main scanner orchestrating all components"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        self.config = self._load_config(config_path)
        self.scraper = ASXAnnouncementScraper()
        self.pdf_analyzer = PDFAnalyzer(self.config)  # NEW: PDF analyzer
        self.analyzer = StockTrendAnalyzer(self.config)
        self.detector = SellOnNewsDetector(self.config)
        self.reporter = ReportGenerator()
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"{Colors.WARNING}Config file not found, using defaults{Colors.ENDC}")
            return {
                "sell_on_news_keywords": ["Record", "All-time high", "Capital raise", "Placement"],
                "buy_signal_keywords": ["Discovery", "High grade", "Contract", "Acquisition"],
                "analysis": {"rsi_overbought": 70, "rsi_oversold": 30},
                "filters": {"price_sensitive_only": True},
                "pdf_analysis": {"enabled": True, "weight": 0.6}
            }
    
    async def run(self, generate_html: bool = True, analyze_pdfs: bool = True) -> List[ScanResult]:
        """Run the full 5-step scanning pipeline"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}ASX Announcement Scanner{Colors.ENDC}")
        print("=" * 50)
        
        # ===== STEP 1: Scrape Price-Sensitive Announcements =====
        # Navigate to ASX announcements page and find all price-sensitive announcements
        print(f"\n{Colors.CYAN}Step 1: Scraping price-sensitive announcements...{Colors.ENDC}")
        price_sensitive_only = self.config.get('filters', {}).get('price_sensitive_only', True)
        announcements = await self.scraper.scrape_announcements(price_sensitive_only)
        
        if not announcements:
            print(f"{Colors.WARNING}No announcements found{Colors.ENDC}")
            return []
        
        # ===== STEP 2: Download & Read PDF Content =====
        # Download each announcement PDF and extract the text content
        pdf_enabled = self.config.get('pdf_analysis', {}).get('enabled', True)
        if analyze_pdfs and pdf_enabled and PDF_SUPPORT:
            print(f"\n{Colors.CYAN}Step 2: Downloading and reading PDF content...{Colors.ENDC}")
            announcements = self.pdf_analyzer.analyze_announcements(announcements)
        else:
            print(f"\n{Colors.WARNING}Step 2: Skipping PDF analysis{Colors.ENDC}")
        
        # ===== STEP 3: Analyse Announcement Sentiment =====
        # Analyze each announcement to determine if it's positive or negative
        print(f"\n{Colors.CYAN}Step 3: Analysing announcement sentiment (parallel)...{Colors.ENDC}")
        results = []
        
        # Get unique symbols for technical analysis
        unique_symbols = list(set(ann.asx_code for ann in announcements))
        analysis_cache = {}
        
        # Use ThreadPoolExecutor for parallel stock data fetching
        print(f"  Fetching data for {len(unique_symbols)} unique stocks...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all stock analysis tasks
            future_to_symbol = {
                executor.submit(self.analyzer.analyze_stock, symbol): symbol 
                for symbol in unique_symbols
            }
            
            # Collect results as they complete
            completed = 0
            for future in future_to_symbol:
                symbol = future_to_symbol[future]
                try:
                    analysis_cache[symbol] = future.result()
                    completed += 1
                    print(f"  [{completed}/{len(unique_symbols)}] Completed {symbol}" + " " * 10, end='\r')
                except Exception as e:
                    print(f"  Error analyzing {symbol}: {e}")
                    analysis_cache[symbol] = None
        
        print(f"  Analysed {len(unique_symbols)} unique stocks" + " " * 30)
        
        # ===== STEP 4: Determine "Sell on News" =====
        # Decide if the announcement is a "sell on news" scenario
        print(f"\n{Colors.CYAN}Step 4: Determining sell-on-news scenarios...{Colors.ENDC}")
        pdf_weight = self.config.get('pdf_analysis', {}).get('weight', 0.6)
        headline_weight = 1 - pdf_weight
        
        for ann in announcements:
            result = ScanResult(announcement=ann, analysis=analysis_cache.get(ann.asx_code))
            
            # Calculate headline + technical scores
            sell_score, sell_reasons = self.detector.calculate_sell_on_news_score(result)
            buy_score, buy_reasons = self.detector.calculate_buy_score(result)
            
            # Integrate PDF content scores if available
            if ann.pdf_analysis:
                pdf_buy = ann.pdf_analysis.get('buy_score', 0)
                pdf_sell = ann.pdf_analysis.get('sell_score', 0)
                pdf_signals = ann.pdf_analysis.get('signals', [])
                
                # Weighted combination: PDF content (60%) + headline/technical (40%)
                buy_score = (buy_score * headline_weight) + (pdf_buy * pdf_weight)
                sell_score = (sell_score * headline_weight) + (pdf_sell * pdf_weight)
                
                # Add PDF signals to reasons
                buy_reasons = [s for s in pdf_signals if '📈' in s] + buy_reasons
                sell_reasons = [s for s in pdf_signals if '📉' in s] + sell_reasons
            
            result.sell_on_news_score = sell_score
            result.buy_score = buy_score
            result.reasons = buy_reasons if buy_score >= sell_score else sell_reasons
            result.classification = self.reporter.classify_result(result)
            
            # Generate short summary
            result.summary = self._generate_summary(ann, result)
            
            results.append(result)
        
        # ===== STEP 5: Rate & Summarize Each Stock =====
        # Output a rating and short summary for each stock
        print(f"\n{Colors.CYAN}Step 5: Generating ratings and summaries...{Colors.ENDC}")
        self.reporter.display_console_report(results)
        
        if generate_html:
            self.reporter.generate_html_report(results)
        
        return results
    
    def _generate_summary(self, ann: Announcement, result: ScanResult) -> str:
        """Generate a short summary for the announcement"""
        parts = []
        
        # Add document type if available
        doc_type = ann.pdf_analysis.get('document_type', 'unknown') if ann.pdf_analysis else 'unknown'
        type_labels = {
            'exploration': 'Exploration update',
            'quarterly': 'Quarterly report',
            'half_year': 'Half-year results',
            'annual': 'Annual report',
            'capital_raise': 'Capital raising',
            'contract': 'Contract/agreement',
            'mna': 'M&A activity',
            'trading_halt': 'Trading halt',
        }
        if doc_type in type_labels:
            parts.append(type_labels[doc_type])
        
        # Add key signals (max 2)
        signals = result.reasons[:2]
        for signal in signals:
            # Clean up emoji prefixes for summary
            clean_signal = signal.replace('📈 ', '').replace('📉 ', '')
            parts.append(clean_signal)
        
        # Add classification reasoning
        if result.classification == 'BUY':
            parts.append('Positive signals dominate')
        elif result.classification == 'SELL_ON_NEWS':
            parts.append('Negative signals dominate')
        else:
            parts.append('Mixed signals')
        
        return '. '.join(parts[:3]) if parts else 'No significant signals detected'


# ============================================================================
# Entry Point
# ============================================================================

def is_market_day() -> tuple[bool, str]:
    """Check if today is a trading day (weekday)"""
    import datetime
    today = datetime.datetime.now()
    day_name = today.strftime('%A')
    
    if today.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False, day_name
    return True, day_name


async def main():
    """Main entry point for the scanner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scan ASX price-sensitive announcements')
    parser.add_argument('--visible', action='store_true', 
                        help='Run browser in visible mode for debugging')
    parser.add_argument('--all', action='store_true',
                        help='Include non-price-sensitive announcements')
    parser.add_argument('--no-html', action='store_true',
                        help='Skip HTML report generation')
    parser.add_argument('--no-pdf', action='store_true',
                        help='Skip PDF content analysis')
    args = parser.parse_args()
    
    # Check if market is open
    is_trading_day, day_name = is_market_day()
    
    if not is_trading_day:
        print(f"\n{Colors.WARNING}Today is {day_name} - ASX market is closed.{Colors.ENDC}")
        print(f"{Colors.WARNING}There may be no new announcements. Attempting to scrape anyway...{Colors.ENDC}\n")
    
    scanner = ASXAnnouncementScanner()
    
    # Override headless mode if --visible flag is set
    if args.visible:
        print(f"{Colors.CYAN}Running in visible browser mode for debugging...{Colors.ENDC}")
        original_scrape = scanner.scraper.scrape_announcements
        async def visible_scrape(price_sensitive_only=True, headless=True):
            return await original_scrape(price_sensitive_only=price_sensitive_only, headless=False)
        scanner.scraper.scrape_announcements = visible_scrape
    
    price_sensitive = not args.all
    generate_html = not args.no_html
    analyze_pdfs = not args.no_pdf
    
    await scanner.run(generate_html=generate_html, analyze_pdfs=analyze_pdfs)


if __name__ == "__main__":
    asyncio.run(main())

