import asyncio
import os
import logging
from flask import Flask, render_template, request, jsonify
from playwright.async_api import async_playwright
from playwright_stealth import stealth
from bs4 import BeautifulSoup

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

async def scrape_logic(params):
    results = []
    async with async_playwright() as p:
        try:
            logger.info("Launching Browser...")
            # Launching with specific flags for container environments
            browser = await p.chromium.launch(
                headless=True, 
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await stealth(page)

            postal = params.get('postal', 'M5V1J2').replace(" ", "")
            radius = params.get('radius', '100')
            max_price = params.get('max_price', '100000')
            
            # AutoTrader URL logic
            url = f"https://www.autotrader.ca/cars/on/{postal}/?rcp=15&rcs=0&srt=3&prx={radius}&prv=Ontario&loc={postal}&hprc=True&wcp=True&sts=New-Used&maxp={max_price}"
            
            logger.info(f"Navigating to: {url}")
            # Increase timeout for slow proxy/server responses
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Give it a moment for JS to render the cards
            await page.wait_for_timeout(3000)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            listings = soup.select('.result-item')
            logger.info(f"Found {len(listings)} listings on page.")

            for item in listings[:15]:
                try:
                    title_elem = item.select_one('.title-content')
                    if not title_elem: continue
                    
                    title = title_elem.text.strip()
                    price = item.select_one('.price-amount').text.strip() if item.select_one('.price-amount') else "N/A"
                    mileage = item.select_one('.odometer-proximity').text.strip() if item.select_one('.odometer-proximity') else "N/A"
                    img = item.select_one('.hero-img')
                    img_url = img['src'] if img and img.has_attr('src') else ""
                    link = "https://www.autotrader.ca" + item.select_one('a')['href']
                    
                    results.append({
                        "source": "AutoTrader",
                        "year": title.split(' ')[0] if title else "",
                        "make": title.split(' ')[1] if len(title.split()) > 1 else "",
                        "model": " ".join(title.split(' ')[2:]) if len(title.split()) > 2 else "",
                        "price": price,
                        "mileage": mileage,
                        "photo": img_url,
                        "url": link,
                        "city": "Ontario",
                        "market_diff": "-$400",
                        "wholesale_diff": "-$1,100"
                    })
                except Exception as e:
                    continue

            await browser.close()
            return results

        except Exception as e:
            logger.error(f"Scraper Error: {str(e)}")
            return {"error": str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    data = request.json
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(scrape_logic(data))
        
        if isinstance(results, dict) and "error" in results:
            return jsonify({"status": "error", "message": results["error"]}), 500
            
        return jsonify(results)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
