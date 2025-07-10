from flask import Flask, request, send_file, jsonify, render_template_string
import os
from io import BytesIO
from datetime import datetime, timedelta
import json
from collections import defaultdict, Counter

app = Flask(__name__)

# Gelişmiş memory storage
email_data = {
    "opens": [],
    "clicks": [],
    "campaigns": defaultdict(lambda: {"sent": 0, "opened": 0, "clicked": 0})
}

# Modern Dashboard Template
DASHBOARD_HTML = """
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .live-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: #10b981;
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .pulse {
            width: 8px;
            height: 8px;
            background: white;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.1); }
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
            cursor: pointer;
            backdrop-filter: blur(10px);
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 100px;
            height: 100px;
            background: linear-gradient(135deg, transparent 50%, rgba(102, 126, 234, 0.1) 50%);
            border-radius: 0 16px 0 0;
        }
        
        .stat-icon {
            width: 60px;
            height: 60px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.75rem;
            margin-bottom: 15px;
        }
        
        .stat-card.purple .stat-icon { background: rgba(102, 126, 234, 0.1); color: #667eea; }
        .stat-card.green .stat-icon { background: rgba(16, 185, 129, 0.1); color: #10b981; }
        .stat-card.orange .stat-icon { background: rgba(251, 146, 60, 0.1); color: #fb923c; }
        .stat-card.red .stat-icon { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 5px;
            line-height: 1;
        }
        
        .stat-label {
            color: #6b7280;
            font-size: 0.875rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .stat-change {
            position: absolute;
            top: 25px;
            right: 25px;
            font-size: 0.875rem;
            font-weight: 600;
        }
        
        .stat-change.positive { color: #10b981; }
        .stat-change.negative { color: #ef4444; }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }
        
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }
        
        .chart-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #1f2937;
        }
        
        .chart-filters {
            display: flex;
            gap: 10px;
        }
        
        .filter-btn {
            padding: 8px 16px;
            border: none;
            background: #f3f4f6;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .filter-btn:hover {
            background: #e5e7eb;
        }
        
        .filter-btn.active {
            background: #667eea;
            color: white;
        }
        
        .table-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 30px;
            overflow: hidden;
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
        
        th {
            background: #f9fafb;
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
            background: #f9fafb;
        }
        
        .email-cell {
            font-weight: 500;
            color: #111827;
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
            width: 120px;
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
        }
        
        .action-btn {
            padding: 8px 16px;
            border: none;
            background: #667eea;
            color: white;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .action-btn:hover {
            background: #5a67d8;
            transform: translateY(-1px);
        }
        
        .time-ago {
            color: #6b7280;
            font-size: 0.875rem;
        }
        
        .campaign-tag {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: #f3f4f6;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .campaign-tag i {
            color: #667eea;
        }
        
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            table {
                font-size: 0.875rem;
            }
            
            th, td {
                padding: 10px;
            }
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
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1>📧 Email Analytics Dashboard</h1>
                    <p style="color: #6b7280; margin-top: 5px;">Gerçek zamanlı email takip ve analiz sistemi</p>
                </div>
                <div style="display: flex; gap: 15px; align-items: center;">
                    <div class="live-badge">
                        <div class="pulse"></div>
                        <span>CANLI</span>
                    </div>
                    <button class="action-btn" onclick="refreshData()">
                        <i class="fas fa-sync-alt"></i> Yenile
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card purple">
                <div class="stat-icon">
                    <i class="fas fa-envelope-open"></i>
                </div>
                <div class="stat-value" id="total-opens">{{ total_opens }}</div>
                <div class="stat-label">Toplam Açılma</div>
                <div class="stat-change positive">+{{ today_opens }}% bugün</div>
            </div>
            
            <div class="stat-card green">
                <div class="stat-icon">
                    <i class="fas fa-users"></i>
                </div>
                <div class="stat-value" id="unique-opens">{{ unique_opens }}</div>
                <div class="stat-label">Benzersiz Açılma</div>
                <div class="stat-change positive">{{ open_rate }}% oran</div>
            </div>
            
            <div class="stat-card orange">
                <div class="stat-icon">
                    <i class="fas fa-mouse-pointer"></i>
                </div>
                <div class="stat-value" id="total-clicks">{{ total_clicks }}</div>
                <div class="stat-label">Link Tıklamaları</div>
                <div class="stat-change positive">{{ click_rate }}% CTR</div>
            </div>
            
            <div class="stat-card red">
                <div class="stat-icon">
                    <i class="fas fa-chart-line"></i>
                </div>
                <div class="stat-value" id="active-campaigns">{{ active_campaigns }}</div>
                <div class="stat-label">Aktif Kampanya</div>
                <div class="stat-change">Son 24 saat</div>
            </div>
        </div>
        
        <!-- Chart -->
        <div class="chart-container">
            <div class="chart-header">
                <h3 class="chart-title">📊 Son 7 Günlük Aktivite</h3>
                <div class="chart-filters">
                    <button class="filter-btn active" onclick="updateChart('week')">7 Gün</button>
                    <button class="filter-btn" onclick="updateChart('day')">24 Saat</button>
                    <button class="filter-btn" onclick="updateChart('month')">30 Gün</button>
                </div>
            </div>
            <canvas id="activityChart" style="max-height: 300px;"></canvas>
        </div>
        
        <!-- Recent Activity Table -->
        <div class="table-container">
            <div class="table-header">
                <h3 class="chart-title">⚡ Son Aktiviteler</h3>
                <button class="action-btn" onclick="exportData()">
                    <i class="fas fa-download"></i> CSV İndir
                </button>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Email</th>
                        <th>Kampanya</th>
                        <th>Aktivite</th>
                        <th>Zaman</th>
                        <th>Engagement</th>
                    </tr>
                </thead>
                <tbody id="activity-table">
                    {% for activity in recent_activities %}
                    <tr>
                        <td class="email-cell">{{ activity.email }}</td>
                        <td>
                            <div class="campaign-tag">
                                <i class="fas fa-tag"></i>
                                {{ activity.campaign[:15] }}...
                            </div>
                        </td>
                        <td>
                            <span class="badge success">
                                <i class="fas fa-envelope-open" style="margin-right: 4px;"></i>
                                AÇILDI
                            </span>
                        </td>
                        <td class="time-ago">{{ activity.time_ago }}</td>
                        <td>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {{ activity.score }}%"></div>
                                </div>
                                <span style="font-size: 0.875rem; font-weight: 600;">{{ activity.score }}%</span>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Chart setup
        const ctx = document.getElementById('activityChart').getContext('2d');
        const chart = new Chart(ctx, {
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
                        cornerRadius: 8,
                        titleFont: {
                            size: 14
                        },
                        bodyFont: {
                            size: 13
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            precision: 0
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
        
        // Auto refresh
        setInterval(() => {
            fetch('/api/stats')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('total-opens').textContent = data.total_opens;
                    document.getElementById('unique-opens').textContent = data.unique_emails;
                });
        }, 5000);
        
        function refreshData() {
            location.reload();
        }
        
        function exportData() {
            window.location.href = '/export/csv';
        }
        
        function updateChart(period) {
            // Chart period değiştirme
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            // Burada chart data'yı güncelle
        }
    </script>
</body>
</html>
"""

@app.route("/")
def dashboard():
    """Gelişmiş dashboard"""
    # İstatistikleri hesapla
    total_opens = len(email_data["opens"])
    unique_emails = len(set([x["email"] for x in email_data["opens"]]))
    total_clicks = len(email_data["clicks"])
    
    # Bugünkü açılmalar
    today = datetime.now().date()
    today_opens = len([x for x in email_data["opens"] 
                      if datetime.fromisoformat(x["time"]).date() == today])
    
    # Aktif kampanyalar
    active_campaigns = len(email_data["campaigns"])
    
    # Oranlar
    open_rate = round((unique_emails / max(total_opens, 1)) * 100, 1)
    click_rate = round((total_clicks / max(total_opens, 1)) * 100, 1)
    
    # Son 7 günlük veri
    daily_data = []
    daily_labels = []
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        count = len([x for x in email_data["opens"] 
                    if datetime.fromisoformat(x["time"]).date() == date])
        daily_data.append(count)
        daily_labels.append(date.strftime("%d %b"))
    
    # Son aktiviteler
    recent_activities = []
    for activity in sorted(email_data["opens"], 
                          key=lambda x: x["time"], 
                          reverse=True)[:10]:
        time_diff = datetime.now() - datetime.fromisoformat(activity["time"])
        if time_diff.days > 0:
            time_ago = f"{time_diff.days} gün önce"
        elif time_diff.seconds > 3600:
            time_ago = f"{time_diff.seconds // 3600} saat önce"
        elif time_diff.seconds > 60:
            time_ago = f"{time_diff.seconds // 60} dakika önce"
        else:
            time_ago = "Az önce"
            
        # Engagement score (basit hesaplama)
        email_opens = len([x for x in email_data["opens"] 
                          if x["email"] == activity["email"]])
        score = min(100, email_opens * 20)
        
        recent_activities.append({
            "email": activity["email"],
            "campaign": activity["campaign"],
            "time_ago": time_ago,
            "score": score
        })
    
    return render_template_string(DASHBOARD_HTML,
        total_opens=total_opens,
        unique_opens=unique_emails,
        total_clicks=total_clicks,
        active_campaigns=active_campaigns,
        today_opens=today_opens,
        open_rate=open_rate,
        click_rate=click_rate,
        daily_labels=json.dumps(daily_labels),
        daily_data=json.dumps(daily_data),
        recent_activities=recent_activities
    )

@app.route("/open")
def track_open():
    """Email açılma takibi"""
    email = request.args.get("email", "unknown")
    campaign = request.args.get("cid", "unknown")
    
    # Kaydet
    email_data["opens"].append({
        "email": email,
        "campaign": campaign,
        "time": datetime.now().isoformat(),
        "ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent', '')
    })
    
    # Kampanya istatistiklerini güncelle
    email_data["campaigns"][campaign]["opened"] += 1
    
    # 1x1 GIF pixel
    gif_data = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    
    return send_file(BytesIO(gif_data), mimetype='image/gif')

@app.route("/click/<link_id>")
def track_click(link_id):
    """Link tıklama takibi"""
    email = request.args.get("email", "unknown")
    campaign = request.args.get("cid", "unknown")
    url = request.args.get("url", "https://example.com")
    
    # Kaydet
    email_data["clicks"].append({
        "email": email,
        "campaign": campaign,
        "link": link_id,
        "time": datetime.now().isoformat(),
        "url": url
    })
    
    # Yönlendir
    return f'<html><head><meta http-equiv="refresh" content="0;url={url}"></head></html>'

@app.route("/api/stats")
def api_stats():
    """JSON API"""
    return jsonify({
        "total_opens": len(email_data["opens"]),
        "unique_emails": len(set([x["email"] for x in email_data["opens"]])),
        "total_clicks": len(email_data["clicks"]),
        "recent": email_data["opens"][-10:][::-1],
        "campaigns": dict(email_data["campaigns"])
    })

@app.route("/export/csv")
def export_csv():
    """CSV export"""
    csv_data = "Email,Campaign,Time,Type\n"
    
    for activity in email_data["opens"]:
        csv_data += f"{activity['email']},{activity['campaign']},{activity['time']},open\n"
    
    for activity in email_data["clicks"]:
        csv_data += f"{activity['email']},{activity['campaign']},{activity['time']},click\n"
    
    return app.response_class(
        response=csv_data,
        status=200,
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment; filename=email_tracking_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
