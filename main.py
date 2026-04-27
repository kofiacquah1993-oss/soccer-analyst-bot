import requests
import os
import time
from datetime import datetime, timedelta

# GitHub pulls these securely from your "Secrets" vault
API_KEY = os.getenv('API_KEY')
TG_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

HEADERS = {'x-apisports-key': API_KEY}
# We scan these leagues for the best value
LEAGUES = [39, 140, 78, 135, 61, 88, 94, 401] 

def run_pro_analysis():
    # Targets the next full day of fixtures
    target_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    all_picks = []

    for league in LEAGUES:
        url = f"https://v3.football.api-sports.io/predictions?league={league}"
        try:
            response = requests.get(url, headers=HEADERS).json().get('response', [])
            for item in response:
                # Filter for tomorrow's games
                if item['fixture']['date'][:10] != target_date: continue
                
                pred = item['predictions']
                h_prob = int(pred['percent']['home'].replace('%',''))
                o_prob = int(pred.get('goals', {}).get('over', "0%").replace('%', ''))
                
                # Selection logic for high-confidence picks
                if h_prob >= 75 or o_prob >= 80:
                    all_picks.append({
                        'match': f"{item['teams']['home']['name']} vs {item['teams']['away']['name']}",
                        'advice': pred['advice'],
                        'confidence': max(h_prob, o_prob)
                    })
            time.sleep(1) # Protect your daily limit
        except:
            continue

    # Pick the top 5 highest confidence games to hit the 5.00 odd target
    top_5 = sorted(all_picks, key=lambda x: x['confidence'], reverse=True)[:5]
    
    if top_5:
        report = f"🏆 **DAILY 5-ODD ANALYST ({target_date})**\n\n"
        for i, p in enumerate(top_5, 1):
            report += f"{i}. **{p['match']}**\n🔥 {p['advice']}\n📊 Conf: {p['confidence']}%\n\n"
        
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": report, "parse_mode": "Markdown"})

if __name__ == "__main__":
    run_pro_analysis()
