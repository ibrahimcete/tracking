from flask import Flask, request, send_file, jsonify, render_template_string, make_response
import os
from io import BytesIO
from datetime import datetime, timedelta
import json
from collections import defaultdict, Counter
import hashlib

app = Flask(__name__)

# Gelişmiş memory storage
tracking_data = {
    "opens": [],
    "clicks": [],
    "campaigns": defaultdict(lambda: {
        "sent": 0, "opened": 0, "clicked": 0, 
        "unique_opens": set(), "unique_clicks": set()
    }),
    "email_stats": defaultdict(lambda: {
        "opens": 0, "clicks": 0, "first_open": None, 
        "last_open": None, "engagement_score": 0
    }),
    "hourly_stats": defaultdict(int),
    "daily_stats": defaultdict(int),
    "device_stats": defaultdict(int),
    "location_stats": defaultdict(int)
}

# Modern Dashboard HTML
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📧 Email Analytics Pro</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #667eea;
            --secondary: #764ba2;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --dark: #1f2937;
            --light: #f9fafb;
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
            backdrop-filter: blur(10px);
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .title {
            font-size: 2.5rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
        }
        
        .subtitle {
            color: #6b7280;
            margin-top: 5px;
        }
        
        .live-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            background: var(--success);
            color: white;
            padding: 8px 20px;
            border-radius: 30px;
            font-weight: 500;
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
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            cursor: pointer;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%);
            animation: rotate 20s linear infinite;
        }
        
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
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
            position: relative;
            z-index: 1;
        }
        
        .stat-card.blue .stat-icon { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
        .stat-card.green .stat-icon { background: rgba(16, 185, 129, 0.1); color: var(--success); }
        .stat-card.orange .stat-icon { background: rgba(245, 158, 11, 0.1); color: var(--warning); }
        .stat-card.purple .stat-icon { background: rgba(139, 92, 246, 0.1); color: #8b5cf6; }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 5px;
            position: relative;
            z-index: 1;
        }
        
        .stat-label {
            color: #6b7280;
            font-size: 0.875rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            position: relative;
            z-index: 1;
        }
        
        .stat-change {
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .stat-change.positive { color: var(--success); }
        .stat-change.negative { color: var(--danger); }
        
        .chart-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 30px;
            backdrop-filter: blur(10px);
        }
        
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .chart-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--dark);
        }
        
        .table-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 30px;
            backdrop-filter: blur(10px);
        }
        
        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
        }
        
        thead {
            background: var(--light);
        }
        
        th {
            padding: 12px 20px;
            text-align: left;
            font-weight: 600;
            font-size: 0.875rem;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 2px solid #e5e7eb;
        }
        
        td {
            padding: 16px 20px;
            border-bottom: 1px solid #f3f4f6;
        }
        
        tr:hover td {
            background: var(--light);
        }
        
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .badge.success { background: #d1fae5; color: #065f46; }
        .badge.warning { background: #fed7aa; color: #92400e; }
        .badge.info { background: #dbeafe; color: #1e40af; }
        .badge.danger { background: #fee2e2; color: #991b1b; }
        
        .progress-bar {
            width: 100px;
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
            transition: width 0.3s ease;
        }
        
        .engagement-score {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        
        .btn-primary:hover {
            background: #5a67d8;
            transform: translateY(-1px);
        }
        
        .device-icon {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #6b7280;
        }
        
        .time-ago {
            color: #6b7280;
            font-size: 0.875rem;
        }
        
        @media (max-width: 768px) {
            .chart-grid {
                grid-template-columns: 1fr;
            }
            
            .title {
                font-size: 2rem;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .footer {
            text-align: center;
            margin-top: 50px;
            color: white;
            opacity: 0.8;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
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
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="header-content">
                <div>
                    <h1 class="title">📧 Email Analytics Pro</h1>
                    <p class="subtitle">Gerçek zamanlı email takip ve analiz sistemi</p>
                </div>
                <div style="display: flex; gap: 15px; align-items: center;">
                    <div class="live-indicator">
                        <div class="pulse"></div>
                        <span>CANLI TAKİP</span>
                    </div>
                    <button class="btn btn-primary" onclick="location.reload()">
                        <i class="fas fa-sync-alt"></i> Yenile
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Stats Cards -->
        <div class="stats-grid">
            <div class="stat-card blue">
                <div class="stat-icon">
                    <i class="fas fa-envelope-open"></i>
                </div>
                <div class="stat-value">{{ total_opens }}</div>
                <div class="stat-label">Toplam Açılma</div>
                <div class="stat-change positive">
                    <i class="fas fa-arrow-up"></i> {{ today_opens }}
                </div>
            </div>
            
            <div class="stat-card green">
                <div class="stat-icon">
                    <i class="fas fa-users"></i>
                </div>
                <div class="stat-value">{{ unique_opens }}</div>
                <div class="stat-label">Benzersiz Açılma</div>
                <div class="stat-change positive">{{ open_rate }}%</div>
            </div>
            
            <div class="stat-card orange">
                <div class="stat-icon">
                    <i class="fas fa-chart-line"></i>
                </div>
                <div class="stat-value">{{ avg_engagement }}%</div>
                <div class="stat-label">Ortalama Engagement</div>
                <div class="stat-change positive">
                    <i class="fas fa-fire"></i> Aktif
                </div>
            </div>
            
            <div class="stat-card purple">
                <div class="stat-icon">
                    <i class="fas fa-clock"></i>
                </div>
                <div class="stat-value">{{ active_24h }}</div>
                <div class="stat-label">Son 24 Saat</div>
                <div class="stat-change">Aktif Email</div>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="chart-grid">
            <div class="chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">📊 Son 7 Günlük Trend</h3>
                </div>
                <canvas id="trendChart" height="300"></canvas>
            </div>
            
            <div class="chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">⏰ Saatlik Dağılım</h3>
                </div>
                <canvas id="hourlyChart" height="300"></canvas>
            </div>
        </div>
        
        <!-- Recent Activity Table -->
        <div class="table-container">
            <div class="table-header">
                <h3 class="chart-title">⚡ Son Aktiviteler</h3>
                <button class="btn btn-primary" onclick="exportData()">
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
                        <th>Cihaz</th>
                        <th>Engagement</th>
                    </tr>
                </thead>
                <tbody>
                    {% for activity in recent_activities %}
                    <tr>
                        <td style="font-weight: 500;">{{ activity.email }}</td>
                        <td>
                            <span class="badge info">{{ activity.campaign }}</span>
                        </td>
                        <td class="time-ago">{{ activity.time_ago }}</td>
                        <td>
                            <div class="device-icon">
                                {% if activity.is_mobile %}
                                    <i class="fas fa-mobile-alt"></i> Mobil
                                {% else %}
                                    <i class="fas fa-desktop"></i> Masaüstü
                                {% endif %}
                            </div>
                        </td>
                        <td>
                            <div class="engagement-score">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {{ activity.engagement }}%"></div>
                                </div>
                                <span style="font-weight: 600;">{{ activity.engagement }}%</span>
                            </div>
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
        
        <div class="footer">
            <p>Email Tracking System © 2024 | Data is stored in memory</p>
        </div>
    </div>
    
    <script>
        // Trend Chart
        const trendCtx = document.getElementById('trendChart').getContext('2d');
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: {{ daily_labels | safe }},
                datasets: [{
                    label: 'Açılmalar',
                    data: {{ daily_data | safe }},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
        
        // Hourly Chart
        const hourlyCtx = document.getElementById('hourlyChart').getContext('2d');
        new Chart(hourlyCtx, {
            type: 'bar',
            data: {
                labels: {{ hourly_labels | safe }},
                datasets: [{
                    label: 'Aktivite',
                    data: {{ hourly_data | safe }},
                    backgroundColor: 'rgba(118, 75, 162, 0.8)',
                    borderRadius: 8
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
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
        
        // Auto refresh every 10 seconds
        setTimeout(() => location.reload(), 10000);
        
        // Export function
        function exportData() {
            window.location.href = '/export/csv';
        }
    </script>
</body>
</html>
'''

def get_device_type(user_agent):
    """User agent'tan cihaz tipi belirle"""
    ua_lower = user_agent.lower() if user_agent else ""
    if any(device in ua_lower for device in ['mobile', 'android', 'iphone', 'ipad']):
        return 'mobile'
    return 'desktop'

def calculate_engagement_score(email):
    """Email için engagement score hesapla"""
    stats = tracking_data["email_stats"][email]
    opens = stats["opens"]
    clicks = stats["clicks"]
    
    # Basit engagement formülü
    score = min(100, (opens * 10) + (clicks * 20))
    return score

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

@app.route("/")
def dashboard():
    """Ana dashboard"""
    # İstatistikleri hesapla
    total_opens = len(tracking_data["opens"])
    unique_opens = len(set(item["email"] for item in tracking_data["opens"]))
    
    # Bugünkü açılmalar
    today = datetime.now().date()
    today_opens = len([
        item for item in tracking_data["opens"] 
        if datetime.fromisoformat(item["time"]).date() == today
    ])
    
    # Son 24 saat
    last_24h = datetime.now() - timedelta(hours=24)
    active_24h = len(set(
        item["email"] for item in tracking_data["opens"] 
        if datetime.fromisoformat(item["time"]) > last_24h
    ))
    
    # Ortalama engagement
    total_engagement = sum(
        calculate_engagement_score(email) 
        for email in tracking_data["email_stats"]
    )
    avg_engagement = round(total_engagement / max(len(tracking_data["email_stats"]), 1))
    
    # Açılma oranı
    open_rate = round((unique_opens / max(total_opens, 1)) * 100, 1)
    
    # Son 7 günlük data
    daily_data = []
    daily_labels = []
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        count = tracking_data["daily_stats"].get(date.isoformat(), 0)
        daily_data.append(count)
        daily_labels.append(date.strftime("%d %b"))
    
    # Saatlik dağılım
    hourly_data = []
    hourly_labels = []
    for hour in range(0, 24, 3):  # 3 saatlik gruplar
        count = sum(tracking_data["hourly_stats"].get(h, 0) for h in range(hour, hour+3))
        hourly_data.append(count)
        hourly_labels.append(f"{hour:02d}:00")
    
    # Son aktiviteler
    recent_activities = []
    for item in sorted(tracking_data["opens"], key=lambda x: x["time"], reverse=True)[:20]:
        engagement = calculate_engagement_score(item["email"])
        is_mobile = get_device_type(item.get("user_agent", "")) == "mobile"
        
        recent_activities.append({
            "email": item["email"],
            "campaign": item["campaign"][:20] + "..." if len(item["campaign"]) > 20 else item["campaign"],
            "time_ago": get_time_ago(item["time"]),
            "is_mobile": is_mobile,
            "engagement": engagement
        })
    
    return render_template_string(DASHBOARD_HTML,
        total_opens=total_opens,
        unique_opens=unique_opens,
        today_opens=today_opens,
        active_24h=active_24h,
        avg_engagement=avg_engagement,
        open_rate=open_rate,
        daily_labels=json.dumps(daily_labels),
        daily_data=json.dumps(daily_data),
        hourly_labels=json.dumps(hourly_labels),
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
    
    # Email istatistiklerini güncelle
    email_stats = tracking_data["email_stats"][email]
    email_stats["opens"] += 1
    if not email_stats["first_open"]:
        email_stats["first_open"] = now.isoformat()
    email_stats["last_open"] = now.isoformat()
    email_stats["engagement_score"] = calculate_engagement_score(email)
    
    # Kampanya istatistikleri
    camp_stats = tracking_data["campaigns"][campaign]
    camp_stats["opened"] += 1
    camp_stats["unique_opens"].add(email)
    
    # Saatlik ve günlük istatistikler
    tracking_data["hourly_stats"][now.hour] += 1
    tracking_data["daily_stats"][now.date().isoformat()] += 1
    
    # Cihaz istatistikleri
    device_type = get_device_type(request.headers.get('User-Agent', ''))
    tracking_data["device_stats"][device_type] += 1
    
    # 1x1 GIF pixel
    gif_data = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    
    response = make_response(send_file(BytesIO(gif_data), mimetype='image/gif'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route("/click/<link_id>")
def track_click(link_id):
    """Link tıklama takibi"""
    email = request.args.get("email", "unknown")
    campaign = request.args.get("cid", "unknown")
    url = request.args.get("url", "https://example.com")
    
    # Tıklamayı kaydet
    tracking_data["clicks"].append({
        "email": email,
        "campaign": campaign,
        "link": link_id,
        "time": datetime.now().isoformat(),
        "url": url
    })
    
    # İstatistikleri güncelle
    tracking_data["email_stats"][email]["clicks"] += 1
    tracking_data["campaigns"][campaign]["clicked"] += 1
    tracking_data["campaigns"][campaign]["unique_clicks"].add(email)
    
    # Yönlendir
    return f'<html><head><meta http-equiv="refresh" content="0;url={url}"></head><body>Yönlendiriliyorsunuz...</body></html>'

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
        "top_emails": sorted(
            [
                {
                    "email": email,
                    "opens": stats["opens"],
                    "clicks": stats["clicks"],
                    "engagement": calculate_engagement_score(email)
                }
                for email, stats in tracking_data["email_stats"].items()
            ],
            key=lambda x: x["engagement"],
            reverse=True
        )[:10],
        "hourly_distribution": dict(tracking_data["hourly_stats"]),
        "device_stats": dict(tracking_data["device_stats"]),
        "recent_activity": tracking_data["opens"][-20:][::-1]
    })

@app.route("/export/csv")
def export_csv():
    """CSV export"""
    csv_data = "Email,Campaign,Time,Opens,Clicks,Engagement Score\n"
    
    # Email bazlı özet
    for email, stats in tracking_data["email_stats"].items():
        campaigns = set(item["campaign"] for item in tracking_data["opens"] if item["email"] == email)
        campaign = ", ".join(campaigns) if campaigns else "N/A"
        
        csv_data += f"{email},{campaign},{stats['last_open'] or 'N/A'},{stats['opens']},{stats['clicks']},{calculate_engagement_score(email)}\n"
    
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = f"attachment; filename=email_tracking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response.headers["Content-Type"] = "text/csv"
    
    return response

@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Email Tracking Server başlatılıyor...")
    print(f"📊 Dashboard: http://0.0.0.0:{port}")
    print(f"📧 Tracking: http://0.0.0.0:{port}/open?email=EMAIL&cid=CAMPAIGN")
    print(f"🔗 API: http://0.0.0.0:{port}/api/stats")
    app.run(host="0.0.0.0", port=port, debug=False)
