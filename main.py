from fastapi import FastAPI, HTTPException
import yfinance as yf
import pandas as pd
import os
import json

from dotenv import load_dotenv
from google import genai
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse



load_dotenv()

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


app = FastAPI(
    title="Autonomous Multi-Agent Stock Analysis API",
    description="AI-powered stock analysis using multiple specialized agents",
    version="1.0.0"
)

app.mount(
    "/static",
    StaticFiles(directory="frontend"),
    name="static"
)

# -----------------------------
# ROOT ENDPOINT
# -----------------------------

@app.get("/")
def root():
    return FileResponse("frontend/index.html")

# -----------------------------
# HEALTH CHECK
# -----------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# -----------------------------
# BASIC STOCK DATA
# -----------------------------

@app.get("/stock/{symbol}")
def get_stock_data(symbol: str):

    try:

        symbol = symbol.upper()

        if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
            ticker_symbol = symbol + ".NS"
        else:
            ticker_symbol = symbol

        ticker = yf.Ticker(ticker_symbol)

        history = ticker.history(period="5d")

        if history.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Stock data not found for {symbol}"
            )

        latest = history.iloc[-1]

        return {
            "symbol": symbol,
            "market_symbol": ticker_symbol,
            "current_price": round(float(latest["Close"]), 2),
            "open": round(float(latest["Open"]), 2),
            "high": round(float(latest["High"]), 2),
            "low": round(float(latest["Low"]), 2),
            "volume": int(latest["Volume"]),
            "data_source": "Yahoo Finance"
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Error fetching stock data: {str(e)}"
        )


# -----------------------------
# TECHNICAL ANALYSIS
# -----------------------------

@app.get("/stock/{symbol}/technical")
def technical_analysis(symbol: str):

    try:

        symbol = symbol.upper()

        if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
            ticker_symbol = symbol + ".NS"
        else:
            ticker_symbol = symbol

        ticker = yf.Ticker(ticker_symbol)

        # Get 6 months of historical data
        history = ticker.history(period="6mo")

        if history.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Stock data not found for {symbol}"
            )

        # -----------------------------
        # SMA 20
        # -----------------------------

        history["SMA_20"] = history["Close"].rolling(
            window=20
        ).mean()

        # -----------------------------
        # EMA 20
        # -----------------------------

        history["EMA_20"] = history["Close"].ewm(
            span=20,
            adjust=False
        ).mean()

        # -----------------------------
        # RSI 14
        # -----------------------------

        delta = history["Close"].diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        average_gain = gain.rolling(window=14).mean()
        average_loss = loss.rolling(window=14).mean()

        rs = average_gain / average_loss

        history["RSI_14"] = 100 - (
            100 / (1 + rs)
        )

        # -----------------------------
        # MACD
        # -----------------------------

        ema_12 = history["Close"].ewm(
            span=12,
            adjust=False
        ).mean()

        ema_26 = history["Close"].ewm(
            span=26,
            adjust=False
        ).mean()

        history["MACD"] = ema_12 - ema_26

        history["MACD_Signal"] = history["MACD"].ewm(
            span=9,
            adjust=False
        ).mean()

        # Get latest values
        latest = history.iloc[-1]

        current_price = float(latest["Close"])
        sma_20 = float(latest["SMA_20"])
        ema_20 = float(latest["EMA_20"])
        rsi = float(latest["RSI_14"])
        macd = float(latest["MACD"])
        macd_signal = float(latest["MACD_Signal"])

        # -----------------------------
        # TREND
        # -----------------------------

        if current_price > sma_20 and current_price > ema_20:
            trend = "BULLISH"

        elif current_price < sma_20 and current_price < ema_20:
            trend = "BEARISH"

        else:
            trend = "NEUTRAL"

        # -----------------------------
        # TRADING SIGNAL
        # -----------------------------

        if (
            trend == "BULLISH"
            and rsi < 70
            and macd > macd_signal
        ):
            signal = "BUY"

        elif (
            trend == "BEARISH"
            and rsi > 30
            and macd < macd_signal
        ):
            signal = "SELL"

        else:
            signal = "HOLD"

        return {

            "symbol": symbol,

            "market_symbol": ticker_symbol,

            "current_price": round(current_price, 2),

            "technical_indicators": {

                "SMA_20": round(sma_20, 2),

                "EMA_20": round(ema_20, 2),

                "RSI_14": round(rsi, 2),

                "MACD": round(macd, 2),

                "MACD_signal": round(macd_signal, 2)

            },

            "trend": trend,

            "signal": signal,

            "data_source": "Yahoo Finance"

        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Technical analysis error: {str(e)}"
        )
    
# -----------------------------
# FUNDAMENTAL ANALYSIS
# -----------------------------

@app.get("/stock/{symbol}/fundamental")
def fundamental_analysis(symbol: str):

    try:

        symbol = symbol.upper()

        if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
            ticker_symbol = symbol + ".NS"
        else:
            ticker_symbol = symbol

        ticker = yf.Ticker(ticker_symbol)

        info = ticker.info

        # Get fundamental information
        revenue = info.get("totalRevenue")
        net_income = info.get("netIncomeToCommon")
        eps = info.get("trailingEps")
        pe_ratio = info.get("trailingPE")
        roe = info.get("returnOnEquity")
        debt = info.get("totalDebt")
        market_cap = info.get("marketCap")

        return {
            "symbol": symbol,
            "market_symbol": ticker_symbol,

            "fundamentals": {
                "revenue": revenue,
                "net_income": net_income,
                "eps": eps,
                "pe_ratio": pe_ratio,
                "roe": roe,
                "total_debt": debt,
                "market_cap": market_cap
            },

            "data_source": "Yahoo Finance"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Fundamental analysis error: {str(e)}"
        )


# -----------------------------
# FUNDAMENTAL AI AGENT
# -----------------------------

@app.get("/stock/{symbol}/fundamental-ai")
def fundamental_ai_analysis(symbol: str):

    try:

        # Convert symbol to uppercase
        symbol = symbol.upper()

        # Indian stock exchange
        if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
            ticker_symbol = symbol + ".NS"
        else:
            ticker_symbol = symbol

        # Get Yahoo Finance data
        ticker = yf.Ticker(ticker_symbol)

        info = ticker.info

        # Fundamental metrics
        revenue = info.get("totalRevenue")
        net_income = info.get("netIncomeToCommon")
        eps = info.get("trailingEps")
        pe_ratio = info.get("trailingPE")
        roe = info.get("returnOnEquity")
        debt = info.get("totalDebt")
        market_cap = info.get("marketCap")

        financial_data = {
            "Revenue": revenue,
            "Net Income": net_income,
            "EPS": eps,
            "P/E Ratio": pe_ratio,
            "ROE": roe,
            "Total Debt": debt,
            "Market Cap": market_cap
        }

        # -----------------------------
        # AI AGENT PROMPT
        # -----------------------------

        prompt = f"""
You are the Fundamental Analysis Agent in a
multi-agent stock analysis system.

Analyze the financial data of {symbol}.

Financial Data:

Revenue: {revenue}
Net Income: {net_income}
EPS: {eps}
P/E Ratio: {pe_ratio}
ROE: {roe}
Total Debt: {debt}
Market Cap: {market_cap}

Your tasks:

1. Explain the company's financial condition.
2. Analyze revenue and net income.
3. Explain the EPS.
4. Analyze the P/E ratio.
5. Discuss debt and financial risk.
6. Discuss ROE if it is available.
7. If any value is null or unavailable, say
   "Data unavailable" instead of guessing.
8. Do not invent financial information.
9. Give an overall fundamental view:
   POSITIVE, NEUTRAL, or NEGATIVE.
10. Do not guarantee future stock returns.
11. Keep the analysis understandable for a student.

Return the analysis using these sections:

Financial Overview:
Profitability:
Valuation:
Risk:
Fundamental View:
Conclusion:
"""

        # -----------------------------
        # GEMINI
        # -----------------------------

        response = gemini_client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        ai_analysis = response.text

        # -----------------------------
        # API RESPONSE
        # -----------------------------

        return {
            "symbol": symbol,
            "market_symbol": ticker_symbol,
            "agent": "Fundamental Analysis Agent",

            "financial_data": financial_data,

            "ai_analysis": ai_analysis,

            "data_source": "Yahoo Finance",
            "ai_model": "Gemini 3 Flash Preview"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Fundamental AI analysis error: {str(e)}"
        )

# -----------------------------
# TECHNICAL AI AGENT
# -----------------------------

@app.get("/stock/{symbol}/technical-ai")
def technical_ai_analysis(symbol: str):

    try:
        symbol = symbol.upper()

        if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
            ticker_symbol = symbol + ".NS"
        else:
            ticker_symbol = symbol

        # Get 6 months of stock data
        ticker = yf.Ticker(ticker_symbol)
        history = ticker.history(period="6mo")

        if history.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Stock data not found for {symbol}"
            )

        # -----------------------------
        # SMA 20
        # -----------------------------

        history["SMA_20"] = history["Close"].rolling(
            window=20
        ).mean()

        # -----------------------------
        # EMA 20
        # -----------------------------

        history["EMA_20"] = history["Close"].ewm(
            span=20,
            adjust=False
        ).mean()

        # -----------------------------
        # RSI 14
        # -----------------------------

        delta = history["Close"].diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        average_gain = gain.rolling(window=14).mean()
        average_loss = loss.rolling(window=14).mean()

        rs = average_gain / average_loss

        history["RSI_14"] = 100 - (
            100 / (1 + rs)
        )

        # -----------------------------
        # MACD
        # -----------------------------

        ema_12 = history["Close"].ewm(
            span=12,
            adjust=False
        ).mean()

        ema_26 = history["Close"].ewm(
            span=26,
            adjust=False
        ).mean()

        history["MACD"] = ema_12 - ema_26

        history["MACD_Signal"] = history["MACD"].ewm(
            span=9,
            adjust=False
        ).mean()

        # Latest values
        latest = history.iloc[-1]

        current_price = float(latest["Close"])
        sma_20 = float(latest["SMA_20"])
        ema_20 = float(latest["EMA_20"])
        rsi = float(latest["RSI_14"])
        macd = float(latest["MACD"])
        macd_signal = float(latest["MACD_Signal"])

        # -----------------------------
        # TREND
        # -----------------------------

        if current_price > sma_20 and current_price > ema_20:
            trend = "BULLISH"

        elif current_price < sma_20 and current_price < ema_20:
            trend = "BEARISH"

        else:
            trend = "NEUTRAL"

        # -----------------------------
        # SIGNAL
        # -----------------------------

        if (
            trend == "BULLISH"
            and rsi < 70
            and macd > macd_signal
        ):
            signal = "BUY"

        elif (
            trend == "BEARISH"
            and rsi > 30
            and macd < macd_signal
        ):
            signal = "SELL"

        else:
            signal = "HOLD"

        # -----------------------------
        # GEMINI PROMPT
        # -----------------------------

        prompt = f"""
You are the Technical Analysis Agent in a
multi-agent stock analysis system.

Analyze the following technical indicators for {symbol}.

Current Price: {current_price}
SMA 20: {sma_20}
EMA 20: {ema_20}
RSI 14: {rsi}
MACD: {macd}
MACD Signal: {macd_signal}
Trend: {trend}
Technical Signal: {signal}

Explain:

1. Price relative to SMA and EMA.
2. RSI and momentum.
3. MACD and momentum direction.
4. Overall technical trend.
5. Strengths and warning signs.
6. Explain the technical signal.

Do not invent any data.
Do not guarantee future returns.
This is technical analysis, not guaranteed financial advice.

Return the response using:

Technical Overview:
Trend Analysis:
Momentum Analysis:
MACD Analysis:
Warning Signs:
Technical View:
Conclusion:
"""

        # -----------------------------
        # GEMINI
        # -----------------------------

        response = gemini_client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        ai_analysis = response.text

        return {
            "symbol": symbol,
            "market_symbol": ticker_symbol,
            "agent": "Technical Analysis Agent",

            "technical_indicators": {
                "current_price": round(current_price, 2),
                "SMA_20": round(sma_20, 2),
                "EMA_20": round(ema_20, 2),
                "RSI_14": round(rsi, 2),
                "MACD": round(macd, 2),
                "MACD_signal": round(macd_signal, 2)
            },

            "trend": trend,
            "signal": signal,

            "ai_analysis": ai_analysis,

            "data_source": "Yahoo Finance",
            "ai_model": "Gemini 3 Flash Preview"
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Technical AI analysis error: {str(e)}"
        )

# -----------------------------
# NEWS & SENTIMENT AI AGENT
# -----------------------------

@app.get("/stock/{symbol}/sentiment-ai")
def sentiment_ai_analysis(symbol: str):

    try:
        symbol = symbol.upper()

        if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
            ticker_symbol = symbol + ".NS"
        else:
            ticker_symbol = symbol

        # Get stock news
        ticker = yf.Ticker(ticker_symbol)
        news = ticker.news

        if not news:
            return {
                "symbol": symbol,
                "agent": "News & Sentiment Agent",
                "message": "No recent news available",
                "sentiment": "NEUTRAL"
            }

        # Extract headlines
        headlines = []

        for item in news[:10]:

            content = item.get("content", {})

            title = content.get("title")

            if title:
                headlines.append(title)

        if not headlines:
            return {
                "symbol": symbol,
                "agent": "News & Sentiment Agent",
                "message": "No readable news headlines available",
                "sentiment": "NEUTRAL"
            }

        news_text = "\n".join(
            f"- {headline}"
            for headline in headlines
        )

        # -----------------------------
        # GEMINI PROMPT
        # -----------------------------

        prompt = f"""
You are the News and Sentiment Analysis Agent
in a multi-agent stock analysis system.

Analyze the following recent news headlines for {symbol}:

{news_text}

Tasks:

1. Analyze the sentiment of the news.
2. Identify positive news.
3. Identify negative news.
4. Identify neutral news.
5. Explain the major factors affecting sentiment.
6. Give an overall sentiment:
   POSITIVE, NEGATIVE, or NEUTRAL.
7. Do not invent news or information.
8. Do not guarantee future stock returns.

Return the response using:

Positive News:
Negative News:
Neutral News:
Major Factors:
Overall Sentiment:
Conclusion:
"""

        # -----------------------------
        # GEMINI
        # -----------------------------

        response = gemini_client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        ai_analysis = response.text

        return {
            "symbol": symbol,
            "market_symbol": ticker_symbol,
            "agent": "News & Sentiment Agent",
            "news_count": len(headlines),
            "headlines": headlines,
            "ai_analysis": ai_analysis,
            "data_source": "Yahoo Finance News",
            "ai_model": "Gemini 3 Flash Preview"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Sentiment analysis error: {str(e)}"
        )

# -----------------------------
# RISK AI AGENT
# -----------------------------

@app.get("/stock/{symbol}/risk-ai")
def risk_ai_analysis(symbol: str):

    try:

        symbol = symbol.upper()

        if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
            ticker_symbol = symbol + ".NS"
        else:
            ticker_symbol = symbol

        # --------------------------------
        # GET FUNDAMENTAL DATA
        # --------------------------------

        ticker = yf.Ticker(ticker_symbol)

        info = ticker.info

        revenue = info.get("totalRevenue")
        net_income = info.get("netIncomeToCommon")
        eps = info.get("trailingEps")
        pe_ratio = info.get("trailingPE")
        roe = info.get("returnOnEquity")
        debt = info.get("totalDebt")
        market_cap = info.get("marketCap")

        # --------------------------------
        # GET TECHNICAL DATA
        # --------------------------------

        history = ticker.history(period="6mo")

        if history.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Stock data not found for {symbol}"
            )

        history["SMA_20"] = history["Close"].rolling(
            window=20
        ).mean()

        history["EMA_20"] = history["Close"].ewm(
            span=20,
            adjust=False
        ).mean()

        delta = history["Close"].diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        average_gain = gain.rolling(
            window=14
        ).mean()

        average_loss = loss.rolling(
            window=14
        ).mean()

        rs = average_gain / average_loss

        history["RSI_14"] = 100 - (
            100 / (1 + rs)
        )

        ema_12 = history["Close"].ewm(
            span=12,
            adjust=False
        ).mean()

        ema_26 = history["Close"].ewm(
            span=26,
            adjust=False
        ).mean()

        history["MACD"] = ema_12 - ema_26

        history["MACD_Signal"] = history["MACD"].ewm(
            span=9,
            adjust=False
        ).mean()

        latest = history.iloc[-1]

        current_price = float(latest["Close"])
        sma_20 = float(latest["SMA_20"])
        ema_20 = float(latest["EMA_20"])
        rsi = float(latest["RSI_14"])
        macd = float(latest["MACD"])
        macd_signal = float(latest["MACD_Signal"])

        # --------------------------------
        # TREND
        # --------------------------------

        if current_price > sma_20 and current_price > ema_20:

            trend = "BULLISH"

        elif current_price < sma_20 and current_price < ema_20:

            trend = "BEARISH"

        else:

            trend = "NEUTRAL"

        # --------------------------------
        # VOLATILITY
        # --------------------------------

        daily_returns = history["Close"].pct_change()

        volatility = daily_returns.std() * (
            252 ** 0.5
        )

        volatility_percentage = volatility * 100

        # --------------------------------
        # RISK PROMPT
        # --------------------------------

        prompt = f"""
You are the Risk Analysis Agent in an autonomous
multi-agent stock analysis system.

Analyze the following information for {symbol}.

Fundamental Data:

Revenue: {revenue}
Net Income: {net_income}
EPS: {eps}
P/E Ratio: {pe_ratio}
ROE: {roe}
Total Debt: {debt}
Market Cap: {market_cap}

Technical Data:

Current Price: {current_price}
SMA 20: {sma_20}
EMA 20: {ema_20}
RSI 14: {rsi}
MACD: {macd}
MACD Signal: {macd_signal}
Trend: {trend}

Volatility:

Annualized Volatility: {volatility_percentage:.2f}%

Your tasks:

1. Identify major financial risks.
2. Identify valuation risks.
3. Identify technical risks.
4. Analyze volatility.
5. Analyze debt-related risk.
6. Identify warning signs.
7. Give an overall risk level:
   LOW, MEDIUM, or HIGH.
8. Explain why the selected risk level was chosen.
9. Do not invent missing data.
10. Do not guarantee future stock performance.

Return the response using:

Financial Risk:
Valuation Risk:
Technical Risk:
Volatility Risk:
Warning Signs:
Overall Risk:
Conclusion:
"""

        # --------------------------------
        # GEMINI
        # --------------------------------

        response = gemini_client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        ai_analysis = response.text

        # --------------------------------
        # RESPONSE
        # --------------------------------

        return {

            "symbol": symbol,

            "market_symbol": ticker_symbol,

            "agent": "Risk Analysis Agent",

            "risk_metrics": {

                "debt": debt,

                "pe_ratio": pe_ratio,

                "rsi": round(rsi, 2),

                "volatility_percentage":
                    round(
                        volatility_percentage,
                        2
                    ),

                "trend": trend

            },

            "ai_risk_analysis": ai_analysis,

            "data_source": "Yahoo Finance",

            "ai_model":
                "Gemini 3 Flash Preview"

        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Risk analysis error: {str(e)}"

        )

# -----------------------------
# FINAL DECISION AI AGENT
# -----------------------------

@app.get("/stock/{symbol}/decision")
def final_decision(symbol: str):

    try:

        symbol = symbol.upper()

        if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
            ticker_symbol = symbol + ".NS"
        else:
            ticker_symbol = symbol

        ticker = yf.Ticker(ticker_symbol)

        # =================================
        # FUNDAMENTAL DATA
        # =================================

        info = ticker.info

        revenue = info.get("totalRevenue")
        net_income = info.get("netIncomeToCommon")
        eps = info.get("trailingEps")
        pe_ratio = info.get("trailingPE")
        roe = info.get("returnOnEquity")
        debt = info.get("totalDebt")
        market_cap = info.get("marketCap")

        # =================================
        # TECHNICAL DATA
        # =================================

        history = ticker.history(period="6mo")

        if history.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Stock data not found for {symbol}"
            )

        history["SMA_20"] = history["Close"].rolling(
            window=20
        ).mean()

        history["EMA_20"] = history["Close"].ewm(
            span=20,
            adjust=False
        ).mean()

        delta = history["Close"].diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        average_gain = gain.rolling(
            window=14
        ).mean()

        average_loss = loss.rolling(
            window=14
        ).mean()

        rs = average_gain / average_loss

        history["RSI_14"] = 100 - (
            100 / (1 + rs)
        )

        ema_12 = history["Close"].ewm(
            span=12,
            adjust=False
        ).mean()

        ema_26 = history["Close"].ewm(
            span=26,
            adjust=False
        ).mean()

        history["MACD"] = ema_12 - ema_26

        history["MACD_Signal"] = history["MACD"].ewm(
            span=9,
            adjust=False
        ).mean()

        latest = history.iloc[-1]

        current_price = float(latest["Close"])
        sma_20 = float(latest["SMA_20"])
        ema_20 = float(latest["EMA_20"])
        rsi = float(latest["RSI_14"])
        macd = float(latest["MACD"])
        macd_signal = float(latest["MACD_Signal"])

        # =================================
        # TECHNICAL SIGNAL
        # =================================

        if current_price > sma_20 and current_price > ema_20:
            trend = "BULLISH"

        elif current_price < sma_20 and current_price < ema_20:
            trend = "BEARISH"

        else:
            trend = "NEUTRAL"

        if (
            trend == "BULLISH"
            and rsi < 70
            and macd > macd_signal
        ):
            technical_signal = "BUY"

        elif (
            trend == "BEARISH"
            and rsi > 30
            and macd < macd_signal
        ):
            technical_signal = "SELL"

        else:
            technical_signal = "HOLD"

        # =================================
        # NEWS
        # =================================

        news = ticker.news

        headlines = []

        for item in news[:10]:

            content = item.get(
                "content",
                {}
            )

            title = content.get("title")

            if title:
                headlines.append(title)

        news_text = "\n".join(
            f"- {headline}"
            for headline in headlines
        )

        # =================================
        # STRUCTURED GEMINI PROMPT
        # =================================

        prompt = f"""
You are the Final Decision Agent in an
autonomous multi-agent stock analysis system.

Analyze {symbol} using the following data.

FUNDAMENTAL DATA:

Revenue: {revenue}
Net Income: {net_income}
EPS: {eps}
P/E Ratio: {pe_ratio}
ROE: {roe}
Debt: {debt}
Market Cap: {market_cap}

TECHNICAL DATA:

Current Price: {current_price}
SMA 20: {sma_20}
EMA 20: {ema_20}
RSI 14: {rsi}
MACD: {macd}
MACD Signal: {macd_signal}

Technical Trend:
{trend}

Technical Signal:
{technical_signal}

RECENT NEWS:

{news_text}

Analyze all available information.

Important rules:

- Do not invent missing information.
- Do not guarantee future returns.
- This is research/decision support, not guaranteed financial advice.
- Fundamental View must be POSITIVE, NEUTRAL, or NEGATIVE.
- Technical View must be BULLISH, NEUTRAL, or BEARISH.
- News View must be POSITIVE, NEUTRAL, or NEGATIVE.
- Risk View must be LOW, MEDIUM, or HIGH.
- Recommendation must be BUY, HOLD, or SELL.
- Confidence must be a number between 0 and 100.

Provide concise but useful explanations.
"""

        # =================================
        # GEMINI STRUCTURED OUTPUT
        # =================================

        response = gemini_client.models.generate_content(

            model="gemini-3-flash-preview",

            contents=prompt,

            config={
                "response_mime_type": "application/json",

                "response_schema": {
                    "type": "object",

                    "properties": {

                        "fundamental_view": {
                            "type": "string"
                        },

                        "fundamental_reason": {
                            "type": "string"
                        },

                        "technical_view": {
                            "type": "string"
                        },

                        "technical_reason": {
                            "type": "string"
                        },

                        "news_view": {
                            "type": "string"
                        },

                        "news_reason": {
                            "type": "string"
                        },

                        "risk_view": {
                            "type": "string"
                        },

                        "risk_reason": {
                            "type": "string"
                        },

                        "overall_view": {
                            "type": "string"
                        },

                        "recommendation": {
                            "type": "string"
                        },

                        "confidence": {
                            "type": "integer"
                        },

                        "reasoning": {
                            "type": "string"
                        },

                        "important_risks": {
                            "type": "string"
                        }
                    },

                    "required": [
                        "fundamental_view",
                        "fundamental_reason",
                        "technical_view",
                        "technical_reason",
                        "news_view",
                        "news_reason",
                        "risk_view",
                        "risk_reason",
                        "overall_view",
                        "recommendation",
                        "confidence",
                        "reasoning",
                        "important_risks"
                    ]
                }
            }
        )

        # =================================
        # CONVERT GEMINI JSON TO PYTHON
        # =================================

        decision = json.loads(response.text)

        # =================================
        # FINAL API RESPONSE
        # =================================

        return {

            "symbol": symbol,

            "market_symbol": ticker_symbol,

            "agent": "Final Decision Agent",

            "fundamental_analysis": {
                "view": decision["fundamental_view"],
                "reason": decision["fundamental_reason"]
            },

            "technical_analysis": {
                "view": decision["technical_view"],
                "reason": decision["technical_reason"],
                "signal": technical_signal,
                "trend": trend
            },

            "news_analysis": {
                "view": decision["news_view"],
                "reason": decision["news_reason"],
                "news_count": len(headlines)
            },

            "risk_analysis": {
                "view": decision["risk_view"],
                "reason": decision["risk_reason"]
            },

            "final_decision": {

                "overall_view":
                    decision["overall_view"],

                "recommendation":
                    decision["recommendation"],

                "confidence":
                    decision["confidence"],

                "reasoning":
                    decision["reasoning"],

                "important_risks":
                    decision["important_risks"]
            },

            "data_source": "Yahoo Finance",

            "ai_model": "Gemini 3 Flash Preview"
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Decision analysis error: {str(e)}"

        )

# ==========================================
# AUTONOMOUS MULTI-AGENT ORCHESTRATOR
# ==========================================

@app.get("/stock/{symbol}/analyze")
def autonomous_stock_analysis(symbol: str):

    try:

        symbol = symbol.upper()

        if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
            ticker_symbol = symbol + ".NS"
        else:
            ticker_symbol = symbol

        ticker = yf.Ticker(ticker_symbol)

        # ==========================================
        # 1. FUNDAMENTAL AGENT
        # ==========================================

        info = ticker.info

        fundamental_data = {
            "revenue": info.get("totalRevenue"),
            "net_income": info.get("netIncomeToCommon"),
            "eps": info.get("trailingEps"),
            "pe_ratio": info.get("trailingPE"),
            "roe": info.get("returnOnEquity"),
            "total_debt": info.get("totalDebt"),
            "market_cap": info.get("marketCap")
        }

        # ==========================================
        # 2. TECHNICAL AGENT
        # ==========================================

        history = ticker.history(period="6mo")

        if history.empty:

            raise HTTPException(
                status_code=404,
                detail=f"Stock data not found for {symbol}"
            )

        history["SMA_20"] = history["Close"].rolling(
            window=20
        ).mean()

        history["EMA_20"] = history["Close"].ewm(
            span=20,
            adjust=False
        ).mean()

        delta = history["Close"].diff()

        gain = delta.where(delta > 0, 0)

        loss = -delta.where(delta < 0, 0)

        average_gain = gain.rolling(
            window=14
        ).mean()

        average_loss = loss.rolling(
            window=14
        ).mean()

        rs = average_gain / average_loss

        history["RSI_14"] = 100 - (
            100 / (1 + rs)
        )

        ema_12 = history["Close"].ewm(
            span=12,
            adjust=False
        ).mean()

        ema_26 = history["Close"].ewm(
            span=26,
            adjust=False
        ).mean()

        history["MACD"] = ema_12 - ema_26

        history["MACD_Signal"] = history["MACD"].ewm(
            span=9,
            adjust=False
        ).mean()

        latest = history.iloc[-1]

        current_price = float(latest["Close"])
        sma_20 = float(latest["SMA_20"])
        ema_20 = float(latest["EMA_20"])
        rsi = float(latest["RSI_14"])
        macd = float(latest["MACD"])
        macd_signal = float(latest["MACD_Signal"])

        if current_price > sma_20 and current_price > ema_20:

            technical_trend = "BULLISH"

        elif current_price < sma_20 and current_price < ema_20:

            technical_trend = "BEARISH"

        else:

            technical_trend = "NEUTRAL"

        if (
            technical_trend == "BULLISH"
            and rsi < 70
            and macd > macd_signal
        ):

            technical_signal = "BUY"

        elif (
            technical_trend == "BEARISH"
            and rsi > 30
            and macd < macd_signal
        ):

            technical_signal = "SELL"

        else:

            technical_signal = "HOLD"

        technical_data = {

            "current_price": round(
                current_price, 2
            ),

            "sma_20": round(
                sma_20, 2
            ),

            "ema_20": round(
                ema_20, 2
            ),

            "rsi_14": round(
                rsi, 2
            ),

            "macd": round(
                macd, 2
            ),

            "macd_signal": round(
                macd_signal, 2
            ),

            "trend": technical_trend,

            "signal": technical_signal

        }

        # ==========================================
        # 3. SENTIMENT AGENT
        # ==========================================

        news = ticker.news

        headlines = []

        for item in news[:10]:

            content = item.get(
                "content",
                {}
            )

            title = content.get(
                "title"
            )

            if title:

                headlines.append(title)

        # ==========================================
        # 4. RISK AGENT
        # ==========================================

        daily_returns = history["Close"].pct_change()

        volatility = (
            daily_returns.std()
            * (252 ** 0.5)
            * 100
        )

        risk_data = {

            "debt":
                fundamental_data["total_debt"],

            "pe_ratio":
                fundamental_data["pe_ratio"],

            "rsi":
                round(rsi, 2),

            "volatility_percentage":
                round(volatility, 2),

            "technical_trend":
                technical_trend

        }

        # ==========================================
        # 5. MULTI-AGENT SYNTHESIS
        # ==========================================

        news_text = "\n".join(
            f"- {headline}"
            for headline in headlines
        )

        prompt = f"""

You are the Lead Decision Agent coordinating
multiple specialized stock-analysis agents.

Stock:
{symbol}

========================================
FUNDAMENTAL AGENT OUTPUT
========================================

Revenue:
{fundamental_data["revenue"]}

Net Income:
{fundamental_data["net_income"]}

EPS:
{fundamental_data["eps"]}

P/E Ratio:
{fundamental_data["pe_ratio"]}

ROE:
{fundamental_data["roe"]}

Debt:
{fundamental_data["total_debt"]}

Market Cap:
{fundamental_data["market_cap"]}


========================================
TECHNICAL AGENT OUTPUT
========================================

Current Price:
{current_price}

SMA 20:
{sma_20}

EMA 20:
{ema_20}

RSI:
{rsi}

MACD:
{macd}

MACD Signal:
{macd_signal}

Trend:
{technical_trend}

Signal:
{technical_signal}


========================================
SENTIMENT AGENT OUTPUT
========================================

Recent Headlines:

{news_text}


========================================
RISK AGENT OUTPUT
========================================

Debt:
{risk_data["debt"]}

P/E:
{risk_data["pe_ratio"]}

RSI:
{risk_data["rsi"]}

Volatility:
{risk_data["volatility_percentage"]}%

Trend:
{risk_data["technical_trend"]}


========================================
FINAL TASK
========================================

Act as the Lead Decision Agent.

Combine all agent outputs.

Identify agreements and disagreements
between the agents.

Determine:

1. Fundamental View
2. Technical View
3. News View
4. Risk View
5. Overall View
6. Recommendation
7. Confidence
8. Reasoning
9. Important Risks

Allowed values:

Fundamental View:
POSITIVE / NEUTRAL / NEGATIVE

Technical View:
BULLISH / NEUTRAL / BEARISH

News View:
POSITIVE / NEUTRAL / NEGATIVE

Risk View:
LOW / MEDIUM / HIGH

Recommendation:
BUY / HOLD / SELL

Confidence:
0-100

Do not guarantee future returns.
Do not invent missing data.
This is decision-support analysis.
"""

        # ==========================================
        # GEMINI
        # ==========================================

        response = gemini_client.models.generate_content(

            model="gemini-3-flash-preview",

            contents=prompt,

            config={

                "response_mime_type":
                    "application/json",

                "response_schema": {

                    "type": "object",

                    "properties": {

                        "fundamental_view": {
                            "type": "string"
                        },

                        "technical_view": {
                            "type": "string"
                        },

                        "news_view": {
                            "type": "string"
                        },

                        "risk_view": {
                            "type": "string"
                        },

                        "overall_view": {
                            "type": "string"
                        },

                        "recommendation": {
                            "type": "string"
                        },

                        "confidence": {
                            "type": "integer"
                        },

                        "reasoning": {
                            "type": "string"
                        },

                        "important_risks": {
                            "type": "string"
                        }

                    },

                    "required": [

                        "fundamental_view",

                        "technical_view",

                        "news_view",

                        "risk_view",

                        "overall_view",

                        "recommendation",

                        "confidence",

                        "reasoning",

                        "important_risks"

                    ]

                }

            }

        )

        final_result = json.loads(
            response.text
        )

        # ==========================================
        # FINAL RESPONSE
        # ==========================================

        return {

            "project":
                "Autonomous Multi-Agent Stock Analysis",

            "symbol":
                symbol,

            "market_symbol":
                ticker_symbol,

            "orchestrator":
                "Active",

            "agents_executed": [

                "Fundamental Agent",

                "Technical Agent",

                "Sentiment Agent",

                "Risk Agent",

                "Decision Agent"

            ],

            "agent_data": {

                "fundamental":
                    fundamental_data,

                "technical":
                    technical_data,

                "sentiment": {

                    "news_count":
                        len(headlines),

                    "headlines":
                        headlines

                },

                "risk":
                    risk_data

            },

            "final_decision": final_result,

            "data_source":
                "Yahoo Finance",

            "ai_model":
                "Gemini 3 Flash Preview"

        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Orchestrator error: {str(e)}"

        )    
    