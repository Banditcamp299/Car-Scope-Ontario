import asyncio
from flask import Flask, render_template, request, jsonify
from playwright.async_api import async_playwright
from playwright_stealth import stealth
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

async def scrape_autotrader(params):
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await stealth(page)

        # Construct URL (Simplified for example)
        # Note: In production, map 'make' and 'postal' into the query string
        postal = params.get('postal', 'M5V1J2').replace(" ", "")
        radius = params.get('radius', '100')
        max_price = params.get('max_price', '50000')
        
        search_url = f"https://www.autotrader.ca/cars/on/{postal}/?rcp=15&rcs=0&srt=3&prx={radius}&prv=Ontario&loc={postal}&hprc=True&wcp=True&sts=New-Used&in_vhr=True&maxp={max_price}"
        
        try:
            await page.goto(search_url, wait_until="networkidle", timeout=60000)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Parsing logic for AutoTrader cards
            listings = soup.select('.result-item')[:10] 
            for item in listings:
                try:
                    title = item.select_one('.title-content').text.strip() if item.select_one('.title-content') else "Unknown"
                    price = item.select_one('.price-amount').text.strip() if item.select_one('.price-amount') else "N/A"
                    mileage = item.select_one('.odometer-proximity').text.strip() if item.select_one('.odometer-proximity') else "N/A"
                    img = item.select_one('.hero-img')['src'] if item.select_one('.hero-img') else ""
                    link = "https://www.autotrader.ca" + item.select_one('a')['href']
                    
                    results.append({
                        "source": "AutoTrader",
                        "year": title.split(' ')[0],
                        "make": title.split(' ')[1],
                        "model": " ".join(title.split(' ')[2:]),
                        "price": price,
                        "mileage": mileage,
                        "photo": img,
                        "url": link,
                        "city": "Ontario",
                        "market_diff": "-$500", # Mock data logic
                        "wholesale_diff": "-$1,200"
                    })
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    data = request.json
    # In a real environment, you'd use a Task Queue like Celery. 
    # For a direct demo, we run the async loop.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(scrape_autotrader(data))
    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
