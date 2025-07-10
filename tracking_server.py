from flask import Flask, request, send_file, jsonify, render_template_string, make_response
import os
from io import BytesIO
from datetime import datetime, timedelta
import json
from collections import defaultdict

app = Flask(__name__)

# Memory storage
tracking_data = {
    "opens": [],
    "email_stats": defaultdict(lambda: {"opens": 0, "first_open": None, "last_open": None}),
    "hourly_stats": defaultdict(int),
    "daily_stats": defaultdict(int)
}

# Dashboard HTML - DÜZGÜN VERSİYON
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📧 Email Tracking Dashboard</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 20px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .stats-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            text-align: center;
        }
        
        .stat-icon {
            font-size: 3rem;
            margin-bottom: 15px;
        }
        
        .stat-icon.blue { color: #3b82f6; }
        .stat-icon.green { color: #10b981; }
        .stat-icon.orange { color: #f59e0b; }
        .stat-icon.purple { color: #8b5cf6; }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #6b7280;
            font-size: 0.9rem;
        }
        
        /* GRAFİKLER İÇİN DÜZGÜN LAYOUT */
        .charts-row {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            width: 100%;
        }
        
        .chart-box {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            flex: 1;
        }
        
        .chart-box.large {
            flex: 2;
        }
        
        .chart-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: #1f2937;
        }
        
        /* Canvas için sabit boyut */
        .chart-wrapper {
            position: relative;
            height: 300px;
            width: 100%;
        }
        
        .table-box {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #f9fafb;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #6b7280;
        }
        
        td {
            padding: 12px;
            border-top: 1px solid #e5e7eb;
        }
        
        .badge {
            background: #dbeafe;
            color: #1e40af;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.875rem;
        }
        
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .btn:hover {
            background: #5a67d8;
        }
        
        .empty {
            text-align: center;
            padding: 60px;
            color: #9ca3af;
        }
        
        /* Mobil uyumluluk */
        @media (max-width: 768px) {
            .charts-row {
                flex-direction: column;
            }
            
            .header h1 {
                font-size: 1.8rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📧 Email Tracking Dashboard</h1>
            <p>Gerçek zamanlı email takip sistemi</p>
        </div>
        
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-icon blue">
                    <i class="fas fa-envelope-open"></i>
                </div>
                <div class="stat-value">{{ total_opens }}</div>
                <div class="stat-label">TOPLAM AÇILMA</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon green">
                    <i class="fas fa-users"></i>
                </div>
                <div class="stat-value">{{ unique_opens }}</div>
                <div class="stat-label">BENZERSİZ EMAIL</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon orange">
                    <i class="fas fa-percentage"></i>
                </div>
                <div class="stat-value">{{ open_rate }}%</div>
                <div class="stat-label">AÇILMA ORANI</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon purple">
                    <i class="fas fa-calendar-day"></i>
                </div>
                <div class="stat-value">{{ today_opens }}</div>
                <div class="stat-label">BUGÜN</div>
            </div>
        </div>
        
        <!-- GRAFİKLER - DÜZGÜN LAYOUT -->
        <div class="charts-row">
            <div class="chart-box large">
                <h3 class="chart-title">📊 Son 7 Gün</h3>
                <div class="chart-wrapper">
                    <canvas id="trendChart"></canvas>
                </div>
            </div>
            
            <div class="chart-box">
                <h3 class="chart-title">⏰ Saatlik Dağılım</h3>
                <div class="chart-wrapper">
                    <canvas id="hourlyChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="table-box">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 class="chart-title">📋 Son Aktiviteler</h3>
                <button class="btn" onclick="window.location.href='/export/csv'">
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
                    </tr>
                </thead>
                <tbody>
                    {% for activity in recent_activities %}
                    <tr>
                        <td>{{ activity.email }}</td>
                        <td><span class="badge">{{ activity.campaign }}</span></td>
                        <td>{{ activity.time_ago }}</td>
                        <td>
                            {% if activity.is_mobile %}
                                <i class="fas fa-mobile"></i> Mobil
                            {% else %}
                                <i class="fas fa-desktop"></i> Desktop
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty">
                <i class="fas fa-inbox" style="font-size: 3rem; margin-bottom: 20px;"></i>
                <p>Henüz email açılmamış</p>
            </div>
            {% endif %}
        </div>
    </div>
    
    <script>
        // Grafik ayarları
        Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        
        // Trend grafiği
        const trendChart = new Chart(document.getElementById('trendChart'), {
            type: 'line',
            data: {
                labels: {{ daily_labels | safe }},
                datasets: [{
                    label: 'Açılmalar',
                    data: {{ daily_data | safe }},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 5,
                    pointHoverRadius: 7
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
        
        // Saatlik grafik
        const hourlyChart = new Chart(document.getElementById('hourlyChart'), {
            type: 'bar',
            data: {
                labels: ['00-06', '06-12', '12-18', '18-24'],
                datasets: [{
                    label: 'Aktivite',
                    data: {{ hourly_data | safe }},
                    backgroundColor: '#764ba2',
                    borderRadius: 6
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
        
        // 30 saniyede bir yenile
        setTimeout(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
'''

def get_time_ago(timestamp):
    """Zaman farkı hesapla"""
    dt = datetime.fromisoformat(timestamp)
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
    """Mobil kontrol"""
    if not user_agent:
        return False
    ua = user_agent.lower()
    return any(d in ua for d in ['mobile', 'android', 'iphone', 'ipad'])

@app.route("/")
def dashboard():
    """Dashboard"""
    # İstatistikler
    total_opens = len(tracking_data["opens"])
    unique_opens = len(set(item["email"] for item in tracking_data["opens"]))
    open_rate = round((unique_opens / max(total_opens, 1)) * 100, 1) if total_opens > 0 else 0
    
    # Bugün
    today = datetime.now().date()
    today_opens = sum(1 for item in tracking_data["opens"] 
                     if datetime.fromisoformat(item["time"]).date() == today)
    
    # 7 günlük veri
    daily_data = []
    daily_labels = []
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        count = tracking_data["daily_stats"].get(date.isoformat(), 0)
        daily_data.append(count)
        daily_labels.append(date.strftime("%d %b"))
    
    # Saatlik veri
    hourly_data = [
        sum(tracking_data["hourly_stats"].get(h, 0) for h in range(0, 6)),
        sum(tracking_data["hourly_stats"].get(h, 0) for h in range(6, 12)),
        sum(tracking_data["hourly_stats"].get(h, 0) for h in range(12, 18)),
        sum(tracking_data["hourly_stats"].get(h, 0) for h in range(18, 24))
    ]
    
    # Son 10 aktivite
    recent_activities = []
    for item in sorted(tracking_data["opens"], key=lambda x: x["time"], reverse=True)[:10]:
        recent_activities.append({
            "email": item["email"],
            "campaign": item["campaign"][:15] + "..." if len(item["campaign"]) > 15 else item["campaign"],
            "time_ago": get_time_ago(item["time"]),
            "is_mobile": is_mobile(item.get("user_agent", ""))
        })
    
    return render_template_string(DASHBOARD_HTML,
        total_opens=total_opens,
        unique_opens=unique_opens,
        open_rate=open_rate,
        today_opens=today_opens,
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
    
    now = datetime.now()
    
    # Kaydet
    tracking_data["opens"].append({
        "email": email,
        "campaign": campaign,
        "time": now.isoformat(),
        "ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent', '')
    })
    
    # İstatistik güncelle
    stats = tracking_data["email_stats"][email]
    stats["opens"] += 1
    if not stats["first_open"]:
        stats["first_open"] = now.isoformat()
    stats["last_open"] = now.isoformat()
    
    # Günlük/Saatlik
    tracking_data["daily_stats"][now.date().isoformat()] += 1
    tracking_data["hourly_stats"][now.hour] += 1
    
    # 1x1 GIF
    gif_data = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    
    response = make_response(send_file(BytesIO(gif_data), mimetype='image/gif'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    
    return response

@app.route("/api/stats")
def api_stats():
    """API endpoint"""
    return jsonify({
        "total_opens": len(tracking_data["opens"]),
        "unique_opens": len(set(item["email"] for item in tracking_data["opens"])),
        "recent": tracking_data["opens"][-10:][::-1]
    })

@app.route("/export/csv")
def export_csv():
    """CSV export"""
    csv_data = "Email,Campaign,Açılma Sayısı,İlk Açılma,Son Açılma\n"
    
    # Email özeti
    email_summary = {}
    for item in tracking_data["opens"]:
        email = item["email"]
        if email not in email_summary:
            email_summary[email] = {
                "campaigns": set(),
                "count": 0,
                "first": item["time"],
                "last": item["time"]
            }
        email_summary[email]["campaigns"].add(item["campaign"])
        email_summary[email]["count"] += 1
        email_summary[email]["last"] = item["time"]
    
    for email, data in email_summary.items():
        campaigns = " / ".join(data["campaigns"])
        csv_data += f'{email},"{campaigns}",{data["count"]},{data["first"]},{data["last"]}\n'
    
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = f"attachment; filename=tracking_{datetime.now().strftime('%Y%m%d')}.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
