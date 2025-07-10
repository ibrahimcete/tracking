from flask import Flask, request, send_file, jsonify, render_template_string, make_response
import os
from io import BytesIO
from datetime import datetime, timedelta
import json
from collections import defaultdict, Counter

app = Flask(__name__)

# Gelişmiş memory storage
tracking_data = {
    "opens": [],
    "clicks": [],
    "campaigns": defaultdict(lambda: {"sent": 0, "opened": 0, "clicked": 0}),
    "email_stats": defaultdict(lambda: {"opens": 0, "clicks": 0, "first_open": None, "last_open": None}),
    "hourly_stats": defaultdict(int),
    "daily_stats": defaultdict(int)
}

# Dashboard HTML
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📧 Email Analytics Dashboard</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .title {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #6b7280;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 25px;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        }
        
        .stat-icon {
            width: 60px;
            height: 60px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.75rem;
            margin-bottom: 15px;
        }
        
        .stat-card.blue .stat-icon { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
        .stat-card.green .stat-icon { background: rgba(16, 185, 129, 0.1); color: #10b981; }
        .stat-card.orange .stat-icon { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
        .stat-card.purple .stat-icon { background: rgba(139, 92, 246, 0.1); color: #8b5cf6; }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #6b7280;
            font-size: 0.875rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
        }
        
        .chart-title {
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 20px;
        }
        
        .table-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 30px;
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #6b7280;
            border-bottom: 2px solid #e5e7eb;
        }
        
        td {
            padding: 16px 12px;
            border-bottom: 1px solid #f3f4f6;
        }
        
        .badge {
            display: inline-flex;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            background: #dbeafe;
            color: #1e40af;
        }
        
        .time-ago {
            color: #6b7280;
            font-size: 0.875rem;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            background: #667eea;
            color: white;
            transition: all 0.2s;
        }
        
        .btn:hover {
            background: #5a67d8;
            transform: translateY(-1px);
        }
        
        .live-indicator {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: #10b981;
            color: white;
            padding: 8px 20px;
            border-radius: 30px;
            font-weight: 500;
            margin-left: 20px;
        }
        
        .pulse {
            width: 10px;
            height: 10px;
            background: white;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
            100% { opacity: 1; transform: scale(1); }
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #6b7280;
        }
        
        .empty-state i {
            font-size: 4rem;
            margin-bottom: 20px;
            opacity: 0.3;
        }
        
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .title {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
                <div>
                    <h1 class="title">📧 Email Analytics Dashboard</h1>
                    <p class="subtitle">Gerçek zamanlı email takip ve analiz sistemi</p>
                </div>
                <div style="display: flex; align-items: center;">
                    <div class="live-indicator">
                        <div class="pulse"></div>
                        <span>CANLI</span>
                    </div>
                    <button class="btn" style="margin-left: 20px;" onclick="location.reload()">
                        <i class="fas fa-sync-alt"></i> Yenile
                    </button>
                </div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card blue">
                <div class="stat-icon">
                    <i class="fas fa-envelope-open"></i>
                </div>
                <div class="stat-value">{{ total_opens }}</div>
                <div class="stat-label">Toplam Açılma</div>
            </div>
            
            <div class="stat-card green">
                <div class="stat-icon">
                    <i class="fas fa-users"></i>
                </div>
                <div class="stat-value">{{ unique_opens }}</div>
                <div class="stat-label">Benzersiz Açılma</div>
            </div>
            
            <div class="stat-card orange">
                <div class="stat-icon">
                    <i class="fas fa-percentage"></i>
                </div>
                <div class="stat-value">{{ open_rate }}%</div>
                <div class="stat-label">Açılma Oranı</div>
            </div>
            
            <div class="stat-card purple">
                <div class="stat-icon">
                    <i class="fas fa-clock"></i>
                </div>
                <div class="stat-value">{{ today_opens }}</div>
                <div class="stat-label">Bugünkü Açılmalar</div>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div class="chart-container">
                <h3 class="chart-title">📊 Son 7 Günlük Trend</h3>
                <canvas id="trendChart" height="300"></canvas>
            </div>
            
            <div class="chart-container">
                <h3 class="chart-title">⏰ Saatlik Dağılım</h3>
                <canvas id="hourlyChart" height="300"></canvas>
            </div>
        </div>
        
        <div class="table-container">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 class="chart-title">⚡ Son Aktiviteler</h3>
                <button class="btn" onclick="exportData()">
                    <i class="fas fa-download"></i> CSV İndir
                </button>
            </div>
            
            {% if recent_activities %}
            <table>
                <thead>
                    <tr>
                        <th>Email</th>
                        <th>Kampanya</th>
                        <th>Zaman</th>
                        <th>IP Adresi</th>
                        <th>Cihaz</th>
                    </tr>
                </thead>
                <tbody>
                    {% for activity in recent_activities %}
                    <tr>
                        <td style="font-weight: 500;">{{ activity.email }}</td>
                        <td><span class="badge">{{ activity.campaign }}</span></td>
                        <td class="time-ago">{{ activity.time_ago }}</td>
                        <td style="color: #6b7280;">{{ activity.ip }}</td>
                        <td>
                            {% if activity.is_mobile %}
                                <i class="fas fa-mobile-alt"></i> Mobil
                            {% else %}
                                <i class="fas fa-desktop"></i> Masaüstü
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h3>Henüz aktivite yok</h3>
                <p>Email açılmaları burada görünecek</p>
            </div>
            {% endif %}
        </div>
    </div>
    
    <script>
        // Trend Chart
        const trendCtx = document.getElementById('trendChart').getContext('2d');
        const trendChart = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: {{ daily_labels | safe }},
                datasets: [{
                    label: 'Açılmalar',
                    data: {{ daily_data | safe }},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
        // Hourly Chart
        const hourlyCtx = document.getElementById('hourlyChart').getContext('2d');
        const hourlyChart = new Chart(hourlyCtx, {
            type: 'bar',
            data: {
                labels: ['00-06', '06-12', '12-18', '18-24'],
                datasets: [{
                    label: 'Aktivite',
                    data: {{ hourly_data | safe }},
                    backgroundColor: '#764ba2'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
        // Auto refresh
        setTimeout(() => location.reload(), 30000);
        
        function exportData() {
            window.location.href = '/export/csv';
        }
    </script>
</body>
</html>
'''

def get_time_ago(timestamp):
    """Zaman farkını hesapla"""
    if isinstance(timestamp, str):
        dt = datetime.fromisoformat(timestamp)
    else:
        dt = timestamp
    
    diff = datetime.now() - dt
    
    if diff.days > 0:
        return f"{diff.days} gün önce"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600} saat önce"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60} dakika önce"
    else:
        return "Az önce"

def is_mobile(user_agent):
    """Mobil cihaz kontrolü"""
    if not user_agent:
        return False
    ua_lower = user_agent.lower()
    return any(device in ua_lower for device in ['mobile', 'android', 'iphone', 'ipad'])

@app.route("/")
def dashboard():
    """Ana dashboard"""
    # İstatistikler
    total_opens = len(tracking_data["opens"])
    unique_opens = len(set(item["email"] for item in tracking_data["opens"]))
    
    # Bugünkü açılmalar
    today = datetime.now().date()
    today_opens = len([
        item for item in tracking_data["opens"] 
        if datetime.fromisoformat(item["time"]).date() == today
    ])
    
    # Açılma oranı
    open_rate = round((unique_opens / max(total_opens, 1)) * 100, 1) if total_opens > 0 else 0
    
    # Son 7 günlük data
    daily_data = []
    daily_labels = []
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        count = tracking_data["daily_stats"].get(date.isoformat(), 0)
        daily_data.append(count)
        daily_labels.append(date.strftime("%d %b"))
    
    # Saatlik dağılım (4 grup)
    hourly_data = [
        sum(tracking_data["hourly_stats"].get(h, 0) for h in range(0, 6)),
        sum(tracking_data["hourly_stats"].get(h, 0) for h in range(6, 12)),
        sum(tracking_data["hourly_stats"].get(h, 0) for h in range(12, 18)),
        sum(tracking_data["hourly_stats"].get(h, 0) for h in range(18, 24))
    ]
    
    # Son 20 aktivite
    recent_activities = []
    for item in sorted(tracking_data["opens"], key=lambda x: x["time"], reverse=True)[:20]:
        recent_activities.append({
            "email": item["email"],
            "campaign": item["campaign"][:20] + "..." if len(item["campaign"]) > 20 else item["campaign"],
            "time_ago": get_time_ago(item["time"]),
            "ip": item.get("ip", "Unknown"),
            "is_mobile": is_mobile(item.get("user_agent", ""))
        })
    
    return render_template_string(DASHBOARD_HTML,
        total_opens=total_opens,
        unique_opens=unique_opens,
        today_opens=today_opens,
        open_rate=open_rate,
        daily_labels=json.dumps(daily_labels),
        daily_data=json.dumps(daily_data),
        hourly_data=json.dumps(hourly_data),
        recent_activities=recent_activities
    )

@app.route("/open")
def track_open():
    """Email açılma takibi"""
    email = request.args.get("email", "unknown")
    campaign = request.args.get("cid", "unknown")
    
    # Timestamp
    now = datetime.now()
    
    # Açılmayı kaydet
    tracking_data["opens"].append({
        "email": email,
        "campaign": campaign,
        "time": now.isoformat(),
        "ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent', '')
    })
    
    # Email istatistikleri
    email_stats = tracking_data["email_stats"][email]
    email_stats["opens"] += 1
    if not email_stats["first_open"]:
        email_stats["first_open"] = now.isoformat()
    email_stats["last_open"] = now.isoformat()
    
    # Kampanya istatistikleri
    tracking_data["campaigns"][campaign]["opened"] += 1
    
    # Saatlik ve günlük istatistikler
    tracking_data["hourly_stats"][now.hour] += 1
    tracking_data["daily_stats"][now.date().isoformat()] += 1
    
    # 1x1 GIF pixel
    gif_data = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    
    response = make_response(send_file(BytesIO(gif_data), mimetype='image/gif'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    
    return response

@app.route("/api/stats")
def api_stats():
    """JSON API endpoint"""
    total_opens = len(tracking_data["opens"])
    unique_opens = len(set(item["email"] for item in tracking_data["opens"]))
    
    return jsonify({
        "total_opens": total_opens,
        "unique_opens": unique_opens,
        "total_clicks": len(tracking_data["clicks"]),
        "campaigns": len(tracking_data["campaigns"]),
        "open_rate": round((unique_opens / max(total_opens, 1)) * 100, 1) if total_opens > 0 else 0,
        "recent_activity": tracking_data["opens"][-10:][::-1]
    })

@app.route("/export/csv")
def export_csv():
    """CSV export"""
    csv_data = "Email,Campaign,Time,Opens\n"
    
    # Email bazlı özet
    email_summary = {}
    for item in tracking_data["opens"]:
        email = item["email"]
        if email not in email_summary:
            email_summary[email] = {
                "campaigns": set(),
                "count": 0,
                "last_time": item["time"]
            }
        email_summary[email]["campaigns"].add(item["campaign"])
        email_summary[email]["count"] += 1
        email_summary[email]["last_time"] = max(email_summary[email]["last_time"], item["time"])
    
    for email, data in email_summary.items():
        campaigns = "/".join(data["campaigns"])
        csv_data += f'{email},"{campaigns}",{data["last_time"]},{data["count"]}\n'
    
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = f"attachment; filename=email_tracking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response.headers["Content-Type"] = "text/csv"
    
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Email Tracking Server başlatılıyor...")
    print(f"📊 Dashboard: http://0.0.0.0:{port}")
    print(f"📧 Tracking: http://0.0.0.0:{port}/open?email=EMAIL&cid=CAMPAIGN")
    print(f"🔗 API: http://0.0.0.0:{port}/api/stats")
    app.run(host="0.0.0.0", port=port, debug=False)
