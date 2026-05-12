import asyncio
from playwright.async_api import async_playwright
import json
from database import add_log, update_job_status

active_jobs = {}

async def run_automation(job_id: str, url: str, goal: str, websocket_manager):
    active_jobs[job_id] = True
    step = 1
    
    async def send_event(event_type: str, message: str):
        nonlocal step
        await add_log(job_id, event_type, message, step)
        await websocket_manager.send_message(job_id, {
            "type": event_type,
            "message": message,
            "step": step,
            "job_id": job_id
        })
        step += 1
        await asyncio.sleep(0.1)
    
    try:
        await send_event("browser.launching", "Starting Playwright Chromium browser...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await send_event("browser.launched", "Chromium browser launched successfully")
            
            page = await browser.new_page()
            
            await send_event("page.navigating", f"Navigating to {url}...")
            await page.goto(url, wait_until="networkidle")
            await send_event("page.loaded", f"Page loaded: {await page.title()}")
            
            screenshot_path = f"/tmp/screenshot_{job_id}.png"
            await page.screenshot(path=screenshot_path)
            await send_event("screenshot.captured", f"Screenshot saved")
            
            await send_event("extracting.data", f"Extracting data for goal: {goal}")
            
            if "product" in goal.lower() or "price" in goal.lower():
                products = await page.evaluate('''
                    () => {
                        const items = [];
                        document.querySelectorAll('.product, .item, article').forEach(el => {
                            const title = el.querySelector('h1, h2, h3, .title')?.innerText || '';
                            const price = el.querySelector('.price, .cost')?.innerText || '';
                            if(title || price) items.push({ title, price });
                        });
                        return items;
                    }
                ''')
                result = {"products": products, "count": len(products)}
            else:
                title = await page.title()
                result = {"title": title, "url": url}
            
            await send_event("data.extracted", f"Extracted {result.get('count', 1)} items")
            
            await browser.close()
            await send_event("browser.closed", "Browser closed successfully")
            
            await update_job_status(job_id, "completed", result)
            await send_event("job.completed", f"Job completed successfully")
            
    except Exception as e:
        error_msg = str(e)
        await update_job_status(job_id, "failed", error=error_msg)
        await send_event("job.failed", f"Job failed: {error_msg}")
    finally:
        active_jobs.pop(job_id, None)