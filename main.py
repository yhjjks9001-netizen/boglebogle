from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles 
import yfinance as yf
import pandas as pd
from typing import List

app = FastAPI(title="ETF 수익률 비교 사이트")

app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/", response_class=HTMLResponse)
def show_webpage():
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>내 주식 사이트</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: sans-serif; padding: 20px; background-color: #f8f9fa; }
            
            .top-container { display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }
            
            .control-panel { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); flex: 2; min-width: 600px; }
            .calculator-panel { background: #e3f2fd; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); flex: 1; border: 2px solid #90caf9; min-width: 300px; }
            
            .control-row { display: flex; align-items: center; margin-bottom: 12px; gap: 10px; flex-wrap: wrap; }
            .control-row:last-child { margin-bottom: 0; }
            
            input, select, button { padding: 8px; font-size: 15px; border: 1px solid #ccc; border-radius: 4px; }
            
            button.primary-btn { background: #007bff; color: white; border: none; cursor: pointer; font-weight: bold; width: 100%; padding: 12px; margin-top: 15px; font-size: 16px;}
            button.primary-btn:hover { background: #0056b3; }
            
            button.calc-btn { background: #1565c0; color: white; border: none; cursor: pointer; font-weight: bold; width: 100%; padding: 10px; margin-top: 10px; }
            button.calc-btn:hover { background: #0d47a1; }

            .chart-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
            
            table { width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: center; font-size: 16px; }
            th { background-color: #007bff; color: white; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            
            .calc-result { margin-top: 15px; padding: 15px; background: white; border-radius: 8px; text-align: center; font-size: 18px; }
            .cagr-info { margin-top: 25px; padding: 15px; background: #e9ecef; border-left: 5px solid #6c757d; border-radius: 5px; font-size: 15px; color: #495057; line-height: 1.6; }
            
            .logo-img { width: 24px; height: 24px; border-radius: 4px; object-fit: contain; background: white; }

            /* 격투 게임 스타일 VS 전광판 디자인 */
            .vs-board { 
                flex: 1; display: flex; align-items: center; justify-content: center; 
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                border-radius: 12px; padding: 15px; color: white; 
                box-shadow: inset 0px 4px 15px rgba(0,0,0,0.3); min-width: 280px; 
            }
            .fighter { display: flex; flex-direction: column; align-items: center; width: 100px; }
            .fighter img { 
                width: 60px; height: 60px; border-radius: 50%; background: white; 
                padding: 5px; object-fit: contain; box-shadow: 0 4px 10px rgba(0,0,0,0.4); 
                margin-bottom: 8px; border: 3px solid #f1c40f; 
            }
            .fighter-name { font-size: 13px; font-weight: bold; text-align: center; line-height: 1.2; word-break: keep-all; }
            .vs-text { 
                font-size: 36px; font-weight: 900; font-style: italic; color: #ff4757; 
                text-shadow: 2px 2px 0px #fff, -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff; 
                margin: 0 15px; 
            }

            /* 💡 스마트 자동완성(Autocomplete) 디자인 */
            .autocomplete-wrapper { position: relative; width: 100%; max-width: 250px; }
            .autocomplete-list { 
                position: absolute; top: 100%; left: 0; right: 0; background: white; 
                border: 1px solid #ccc; border-radius: 4px; z-index: 1000; 
                max-height: 250px; overflow-y: auto; list-style: none; padding: 0; margin: 0;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: none;
            }
            .autocomplete-item { padding: 10px; cursor: pointer; border-bottom: 1px solid #eee; display: flex; align-items: center; justify-content: space-between; }
            .autocomplete-item:hover { background-color: #f0f8ff; }
            .item-name { font-weight: bold; font-size: 14px; color: #333; }
            .item-ticker { color: #888; font-size: 12px; }
        </style>
    </head>
    <body>
        <h2>📈 주식 수익률 대시보드 & 타임머신 계산기</h2>
        
        <div class="top-container">
            <div class="control-panel">
                <h3 style="margin-top:0;">📊 1:1 비교 차트 설정</h3>
                
                <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                    <div style="flex: 1; min-width: 320px;">
                        <div class="control-row">
                            <label>🥇 <b>기준 지수:</b></label>
                            <select id="base_ticker" onchange="updateVSBoard()">
                                <option value="VOO">VOO (S&P 500)</option>
                                <option value="QQQ">QQQ (나스닥 100)</option>
                            </select>
                            
                            <label style="margin-left: 10px;">⏱️ <b>주기:</b></label>
                            <select id="interval">
                                <option value="1d">일별</option>
                                <option value="1mo">월별</option>
                                <option value="1y">연별</option>
                            </select>
                        </div>
                        
                        <div class="control-row">
                            <label>📅 <b>기간:</b></label>
                            <input type="date" id="start_date" value="2020-01-01" style="width: 110px;"> ~ 
                            <input type="date" id="end_date" value="2026-05-25" style="width: 110px;">
                        </div>
                        
                        <div class="control-row" style="align-items: flex-start;">
                            <label style="margin-top: 8px;">🔍 <b>비교 종목:</b></label>
                            <div style="display: flex; align-items: center; gap: 8px; flex: 1;">
                                <img id="logo_comp1" class="logo-img" src="" style="display: none;">
                                <div class="autocomplete-wrapper">
                                    <input type="text" id="comp1" placeholder="한글/영문 기업명 검색" value="미국 배당성장 (SCHD)" style="width: 100%; box-sizing: border-box;" oninput="handleAutocomplete('comp1', 'list_comp1', 'logo_comp1')">
                                    <ul id="list_comp1" class="autocomplete-list"></ul>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="vs-board">
                        <div class="fighter" id="vs_base">
                            <img id="vs_base_img" src="">
                            <div class="fighter-name" id="vs_base_name">S&P 500</div>
                        </div>
                        <div class="vs-text">VS</div>
                        <div class="fighter" id="vs_comp">
                            <img id="vs_comp_img" src="" style="display: none;">
                            <div class="fighter-name" id="vs_comp_name"></div>
                        </div>
                    </div>
                </div>
                
                <button class="primary-btn" onclick="drawChart()">대결 시작 (차트 그리기) 🚀</button>
            </div>

            <div class="calculator-panel">
                <h3 style="margin-top:0;">⏳ 타임머신 계산기</h3>
                <div class="control-row">
                    <label style="width: 80px;">투자 원금:</label>
                    <input type="number" id="calc_amount" value="10000000" style="width: 140px;"> 원
                </div>
                <div class="control-row">
                    <label style="width: 80px;">투자 종목:</label>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <img id="logo_calc" class="logo-img" src="" style="display: none;">
                        <div class="autocomplete-wrapper" style="width: 120px;">
                            <input type="text" id="calc_ticker" value="S&P 500 (VOO)" style="width: 100%; box-sizing: border-box;" placeholder="종목 검색" oninput="handleAutocomplete('calc_ticker', 'list_calc', 'logo_calc')">
                            <ul id="list_calc" class="autocomplete-list"></ul>
                        </div>
                    </div>
                </div>
                <div class="control-row">
                    <label style="width: 80px;">투자일자:</label>
                    <input type="date" id="calc_start_date" value="2020-01-01" style="width: 140px;">
                </div>
                <div class="control-row">
                    <label style="width: 80px;">회수일자:</label>
                    <input type="date" id="calc_end_date" value="2026-05-25" style="width: 140px;">
                </div>
                
                <button class="calc-btn" onclick="calculateInvestment()">결과 확인하기 💰</button>
                <div class="calc-result" id="calc_result">버튼을 눌러보세요!</div>
            </div>
        </div>

        <div class="chart-container">
            <canvas id="myChart" width="800" height="300"></canvas>
        </div>
        
        <table id="summaryTable">
            <thead>
                <tr>
                    <th>종목 이름</th>
                    <th>총 누적 수익률 (%)</th>
                    <th>연평균 수익률 (CAGR, %)</th>
                </tr>
            </thead>
            <tbody id="tableBody"></tbody>
        </table>
        
        <div class="cagr-info">
            <strong>* CAGR (Compound Annual Growth Rate, 연평균 복리 수익률) 이란?</strong><br>
            투자기간 동안 매년 평균적으로 몇 %씩 성장했는지를 '복리'를 기준으로 계산한 수치입니다. 주식 시장처럼 매년 오르고 내림이 반복될 때 단순 평균을 내면 수익률이 왜곡될 수 있는데, CAGR은 이러한 착시를 제거해주어 <b>가장 정확한 장기 투자 성과 지표</b>로 사용됩니다.
        </div>
        
        <script>
            let chartInstance = null; 

            // 💡 스마트 사전을 탑재했습니다. (한글, 영문, 별명 모두 지원)
            const stockDb = [
                { ticker: "AAPL", names: ["애플", "APPLE"] },
                { ticker: "MSFT", names: ["마이크로소프트", "MICROSOFT", "마소"] },
                { ticker: "TSLA", names: ["테슬라", "TESLA"] },
                { ticker: "NVDA", names: ["엔비디아", "NVIDIA"] },
                { ticker: "GOOGL", names: ["구글", "알파벳", "GOOGLE"] },
                { ticker: "AMZN", names: ["아마존", "AMAZON"] },
                { ticker: "META", names: ["메타", "페이스북", "META", "FACEBOOK"] },
                { ticker: "SCHD", names: ["미국 배당성장", "SCHWAB", "슈드"] },
                { ticker: "VOO", names: ["S&P 500", "뱅가드", "VANGUARD"] },
                { ticker: "QQQ", names: ["나스닥 100", "인베스코", "NASDAQ"] },
                { ticker: "005930.KS", names: ["삼성전자", "SAMSUNG"] },
                { ticker: "000660.KS", names: ["SK하이닉스", "SK HYNIX"] },
                { ticker: "360750.KS", names: ["TIGER 미국S&P500"] },
                { ticker: "379800.KS", names: ["KODEX 미국나스닥100TR"] },
                { ticker: "458730.KS", names: ["TIGER 미국배당다우존스"] },
                { ticker: "035420.KS", names: ["네이버", "NAVER"] },
                { ticker: "035720.KS", names: ["카카오", "KAKAO"] },
                { ticker: "005380.KS", names: ["현대차", "HYUNDAI"] }
            ];

            const logoMap = {
                "VOO": "vanguard.com", "QQQ": "invesco.com", "SCHD": "schwab.com",
                "AAPL": "apple.com", "TSLA": "tesla.com", "NVDA": "nvidia.com", "MSFT": "microsoft.com", "GOOGL": "google.com", "AMZN": "amazon.com", "META": "meta.com",
                "360750.KS": "miraeasset.com", "458730.KS": "miraeasset.com", 
                "379800.KS": "samsungfund.com", "005930.KS": "samsung.com", "000660.KS": "skhynix.com",
                "035420.KS": "naver.com", "035720.KS": "kakaocorp.com", "005380.KS": "hyundai.com"
            };

            // 💡 자동완성(추천검색어) 구동 엔진
            function handleAutocomplete(inputId, listId, imgId) {
                const input = document.getElementById(inputId);
                const list = document.getElementById(listId);
                const query = input.value.trim().toUpperCase();

                if (query === "") {
                    list.style.display = "none";
                    updateLogo(inputId, imgId);
                    if(inputId === 'comp1') updateVSBoard();
                    return;
                }

                // 입력값과 매칭되는 종목 찾기
                const matches = stockDb.filter(item => 
                    item.ticker.includes(query) || 
                    item.names.some(name => name.toUpperCase().includes(query))
                );

                list.innerHTML = "";
                if (matches.length > 0) {
                    matches.forEach(match => {
                        const li = document.createElement("li");
                        li.className = "autocomplete-item";
                        li.innerHTML = `<span class="item-name">${match.names[0]}</span> <span class="item-ticker">${match.ticker}</span>`;
                        // 리스트 항목 클릭 시 자동 완성 적용
                        li.onclick = () => {
                            input.value = `${match.names[0]} (${match.ticker})`;
                            list.style.display = "none";
                            updateLogo(inputId, imgId);
                            if(inputId === 'comp1') updateVSBoard();
                        };
                        list.appendChild(li);
                    });
                    list.style.display = "block";
                } else {
                    list.style.display = "none";
                }
                
                updateLogo(inputId, imgId);
                if(inputId === 'comp1') updateVSBoard();
            }

            // 바탕을 클릭하면 자동완성 창 닫기
            document.addEventListener("click", function (e) {
                if (!e.target.closest(".autocomplete-wrapper")) {
                    document.querySelectorAll(".autocomplete-list").forEach(list => list.style.display = "none");
                }
            });

            // 💡 입력값에서 완벽하게 티커(종목코드)만 추출하거나 번역하는 함수
            function extractTicker(inputStr) {
                // 1. "애플 (AAPL)" 처럼 괄호가 있으면 괄호 안의 티커 우선 추출
                const match = inputStr.match(/\(([^)]+)\)$/);
                if (match) return match[1].trim().toUpperCase();

                // 2. 괄호 없이 "삼성전자" 또는 "마소"라고만 적은 경우, 사전에서 티커로 번역
                const searchStr = inputStr.trim().toUpperCase();
                for (const item of stockDb) {
                    if (item.ticker === searchStr) return item.ticker;
                    for (const name of item.names) {
                        if (name.toUpperCase() === searchStr) return item.ticker;
                    }
                }
                // 3. 사전에 없으면 입력한 글자 그대로 반환 (사용자가 직접 티커를 입력한 경우)
                return searchStr; 
            }

            function createFallbackSVG(text) {
                const char = (text || "?").charAt(0).toUpperCase();
                const colors = ['#e53935', '#d81b60', '#8e24aa', '#3949ab', '#1e88e5', '#00897b', '#43a047', '#f4511e'];
                const bgColor = colors[char.charCodeAt(0) % colors.length];
                const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                    <rect width="100" height="100" fill="${bgColor}"/>
                    <text x="50%" y="50%" font-size="45" fill="white" font-family="sans-serif" font-weight="bold" text-anchor="middle" dominant-baseline="central">${char}</text>
                </svg>`;
                return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
            }

            function updateLogo(inputId, imgId) {
                const inputVal = document.getElementById(inputId).value;
                const imgEl = document.getElementById(imgId);
                
                if(inputVal.trim() === "") {
                    imgEl.style.display = 'none';
                    return;
                }
                
                const ticker = extractTicker(inputVal);
                const dispName = inputVal.split('(')[0].trim() || ticker;
                
                imgEl.style.display = 'inline';
                if (logoMap[ticker]) {
                    imgEl.src = `https://logo.clearbit.com/${logoMap[ticker]}?size=40`;
                    imgEl.onerror = function() {
                        this.onerror = null; 
                        this.src = createFallbackSVG(dispName);
                    };
                } else {
                    imgEl.src = createFallbackSVG(dispName);
                }
            }

            function updateVSBoard() {
                const baseVal = document.getElementById('base_ticker').value;
                const baseImg = document.getElementById('vs_base_img');
                const baseName = document.getElementById('vs_base_name');
                
                if(baseVal === 'VOO') {
                    baseName.innerText = 'S&P 500';
                    baseImg.src = '/static/슨피로고.jpg';
                    baseImg.style.display = 'block';
                } else {
                    baseName.innerText = 'NASDAQ 100';
                    baseImg.src = '/static/나스닥로고.png';
                    baseImg.style.display = 'block';
                }

                const comp1Val = document.getElementById('comp1').value;
                const compImg = document.getElementById('vs_comp_img');
                const compName = document.getElementById('vs_comp_name');

                if(comp1Val.trim() !== "") {
                    const ticker = extractTicker(comp1Val);
                    const dispName = comp1Val.split('(')[0].trim() || ticker; 

                    compImg.style.display = 'block';
                    if(logoMap[ticker]) {
                        compImg.src = `https://logo.clearbit.com/${logoMap[ticker]}?size=100`;
                        compImg.onerror = function() {
                            this.onerror = null;
                            this.src = createFallbackSVG(dispName);
                        };
                    } else {
                        compImg.src = createFallbackSVG(dispName);
                    }
                    compName.innerText = dispName;
                } else {
                    compImg.style.display = 'none';
                    compName.innerText = '';
                }
            }

            window.onload = function() {
                updateLogo('comp1', 'logo_comp1');
                updateLogo('calc_ticker', 'logo_calc');
                updateVSBoard(); 
            };

            function calculateInvestment() {
                const amount = document.getElementById('calc_amount').value;
                const ticker = extractTicker(document.getElementById('calc_ticker').value);
                const calcStartDate = document.getElementById('calc_start_date').value;
                const calcEndDate = document.getElementById('calc_end_date').value;
                
                if(!ticker) { alert("투자 종목을 입력해주세요!"); return; }
                
                const resultBox = document.getElementById('calc_result');
                resultBox.innerHTML = "과거로 돌아가 투자하는 중... 🚀";
                
                fetch(`/api/calculate?ticker=${ticker}&start_date=${calcStartDate}&end_date=${calcEndDate}&amount=${amount}`)
                    .then(res => res.json())
                    .then(result => {
                        if(result.status === 'success') {
                            const finalMoney = Math.round(result.final_amount).toLocaleString('ko-KR');
                            const returnPct = result.return_pct.toFixed(2);
                            const color = result.return_pct >= 0 ? 'red' : 'blue';
                            
                            let html = `<strong>결과 금액: <span style="color:${color}">₩${finalMoney}</span></strong><br>`;
                            html += `<span style="font-size:14px; color:${color}">수익률: ${returnPct}%</span>`;
                            resultBox.innerHTML = html;
                        } else {
                            resultBox.innerHTML = "❌ 해당 기간의 데이터를 찾을 수 없습니다.";
                        }
                    })
                    .catch(e => { resultBox.innerHTML = "오류가 발생했습니다."; });
            }

            function drawChart() {
                const baseTicker = document.getElementById('base_ticker').value;
                const interval = document.getElementById('interval').value;
                const startDate = document.getElementById('start_date').value;
                const endDate = document.getElementById('end_date').value;
                
                const comp1 = extractTicker(document.getElementById('comp1').value);
                
                let tickerArray = [baseTicker];
                if(comp1 !== "") tickerArray.push(comp1);
                tickerArray = [...new Set(tickerArray)];

                let url = `/api/returns?start_date=${startDate}&end_date=${endDate}&interval=${interval}`;
                tickerArray.forEach(t => { url += `&tickers=${t}` });

                fetch(url)
                    .then(response => response.json())
                    .then(result => {
                        const data = result.data;
                        const rawPrices = result.raw_prices;
                        
                        const tickers = Object.keys(data);
                        const dates = Object.keys(data[tickers[0]]);
                        
                        const datasets = tickers.map((ticker, index) => {
                            return {
                                label: ticker,
                                data: Object.values(data[ticker]),
                                borderWidth: index === 0 ? 4 : 2,
                                pointRadius: interval === '1d' ? 0 : 3 
                            }
                        });

                        if(chartInstance) { chartInstance.destroy(); }
                        
                        chartInstance = new Chart(document.getElementById('myChart'), {
                            type: 'line',
                            data: { labels: dates, datasets: datasets },
                            options: {
                                plugins: {
                                    tooltip: {
                                        callbacks: {
                                            label: function(context) {
                                                const ticker = context.dataset.label;
                                                const date = context.label;
                                                const returnPct = (context.parsed.y - 100).toFixed(2);
                                                const rawPrice = rawPrices[ticker][date];
                                                
                                                if (ticker.endsWith('.KS') || ticker.endsWith('.KQ')) {
                                                    return `${ticker}: ${returnPct}% (₩${Math.round(rawPrice).toLocaleString('ko-KR')})`;
                                                } else {
                                                    return `${ticker}: ${returnPct}% ($${rawPrice.toFixed(2)})`;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        });

                        const tbody = document.getElementById('tableBody');
                        tbody.innerHTML = ''; 

                        const start = new Date(dates[0]);
                        const end = new Date(dates[dates.length - 1]);
                        const years = (end - start) / (1000 * 60 * 60 * 24 * 365.25) || 1;

                        tickers.forEach(ticker => {
                            const prices = Object.values(data[ticker]);
                            const finalPrice = prices[prices.length - 1]; 

                            const totalReturn = (finalPrice - 100).toFixed(2);
                            const cagr = ((Math.pow(finalPrice / 100, 1 / years) - 1) * 100).toFixed(2);

                            const colorTotal = totalReturn >= 0 ? 'red' : 'blue';
                            const colorCagr = cagr >= 0 ? 'red' : 'blue';

                            const isBase = ticker === baseTicker;
                            const displayName = isBase ? `🥇 ${ticker}` : ticker;

                            const row = `<tr>
                                <td><strong>${displayName}</strong></td>
                                <td style="color: ${colorTotal}; font-weight: bold;">${totalReturn}%</td>
                                <td style="color: ${colorCagr}; font-weight: bold;">${cagr}%</td>
                            </tr>`;
                            tbody.innerHTML += row;
                        });
                    });
            }
            
            drawChart();
        </script>
    </body>
    </html>
    """
    return html_code

@app.get("/api/calculate")
def calculate_investment(ticker: str, start_date: str, end_date: str, amount: float):
    try:
        stock_data = yf.download(ticker, start=start_date, end=end_date)['Close']
        if stock_data.empty: return {"status": "error"}
            
        start_price = float(stock_data.iloc[0].iloc[0] if isinstance(stock_data, pd.DataFrame) else stock_data.iloc[0])
        end_price = float(stock_data.iloc[-1].iloc[0] if isinstance(stock_data, pd.DataFrame) else stock_data.iloc[-1])
        is_korean = ticker.endswith('.KS') or ticker.endswith('.KQ')
        
        if is_korean:
            final_krw = (amount / start_price) * end_price
        else:
            fx_data = yf.download("KRW=X", start=start_date, end=end_date)['Close']
            if fx_data.empty: return {"status": "error"}
            fx_start = float(fx_data.iloc[0].iloc[0] if isinstance(fx_data, pd.DataFrame) else fx_data.iloc[0])
            fx_end = float(fx_data.iloc[-1].iloc[0] if isinstance(fx_data, pd.DataFrame) else fx_data.iloc[-1])
            
            usd_invested = amount / fx_start
            shares = usd_invested / start_price
            usd_final = shares * end_price
            final_krw = usd_final * fx_end

        return_pct = ((final_krw - amount) / amount) * 100
        return {"status": "success", "final_amount": final_krw, "return_pct": return_pct}
    except:
        return {"status": "error"}

@app.get("/api/returns")
def get_etf_returns(
    tickers: List[str] = Query(["VOO"]),
    start_date: str = "2020-01-01",
    end_date: str = "2026-05-25",
    interval: str = "1d"
):
    data = yf.download(tickers, start=start_date, end=end_date)['Close']
    if isinstance(data, pd.Series): data = data.to_frame(tickers[0])
    data = data.dropna()

    if interval == "1mo":
        try: data = data.resample('ME').last()
        except: data = data.resample('M').last()
    elif interval == "1y":
        try: data = data.resample('YE').last()
        except: data = data.resample('Y').last()
    data = data.dropna()
    
    raw_prices = data.copy()
    raw_prices.index = raw_prices.index.strftime('%Y-%m-%d')
    normalized = (data / data.iloc[0]) * 100
    normalized.index = normalized.index.strftime('%Y-%m-%d')
    
    return {"status": "success", "data": normalized.to_dict(), "raw_prices": raw_prices.to_dict()}