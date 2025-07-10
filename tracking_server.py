# tracking_server.py - Gelişmiş Email Tracking Sistemi
from flask import Flask, request, send_file, jsonify, render_template_string, redirect
import sqlite3
import datetime
import os
import json
from urllib.parse import urlparse
import hashlib
import base64
from io import BytesIO
from PIL import Image
import user_agents

app = Flask(__name__)

# Konfigürasyon
DB = "tracking.db"
PIXEL_PATH = "pixel.gif"
SECRET_KEY = "25268338iiC*"  # Değiştirin!
import os
print("\n" + "="*50)
print("[DEBUG] TRACKING SERVER BAŞLIYOR")
print(f"[DEBUG] Çalışma dizini: {os.getcwd()}")
print(f"[DEBUG] Script dizini: {os.path.dirname(os.path.abspath(__file__))}")
print(f"[DEBUG] Veritabanı yolu: {os.path.abspath(DB)}")
print(f"[DEBUG] Dosya var mı: {os.path.exists(DB)}")

# Test - kaç kayıt var?
if os.path.exists(DB):
    import sqlite3
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM opens")
    count = c.fetchone()[0]
    conn.close()
    print(f"[DEBUG] Opens tablosunda {count} kayıt var")
else:
    print("[DEBUG] tracking.db BULUNAMADI!")
print("="*50 + "\n")
# HTML Dashboard Template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>📧 Email Tracking Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #2c3e50;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.12);
        }
        
        .stat-card .icon {
            width: 50px;
            height: 50px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }
        
        .stat-card.blue .icon { background: #e3f2fd; color: #2196f3; }
        .stat-card.green .icon { background: #e8f5e9; color: #4caf50; }
        .stat-card.orange .icon { background: #fff3e0; color: #ff9800; }
        .stat-card.purple .icon { background: #f3e5f5; color: #9c27b0; }
        
        .stat-card .label {
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }
        
        .stat-card .value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #2c3e50;
        }
        
        .stat-card .change {
            font-size: 0.85rem;
            margin-top: 0.5rem;
        }
        
        .change.positive { color: #4caf50; }
        .change.negative { color: #f44336; }
        
        .chart-container {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            margin-bottom: 2rem;
            max-height: 500px;
            overflow: hidden;
        }
        
        .table-container {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            overflow-x: auto;
            margin-bottom: 2rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #f8f9fa;
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            color: #5a6c7d;
            border-bottom: 2px solid #e9ecef;
        }
        
        td {
            padding: 1rem;
            border-bottom: 1px solid #f1f3f5;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .badge.success { background: #d4edda; color: #155724; }
        .badge.warning { background: #fff3cd; color: #856404; }
        .badge.info { background: #d1ecf1; color: #0c5460; }
        .badge.danger { background: #f8d7da; color: #721c24; }
        
        .live-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
            color: #4caf50;
        }
        
        .live-dot {
            width: 8px;
            height: 8px;
            background: #4caf50;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .email-link {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }
        
        .email-link:hover {
            text-decoration: underline;
        }
        
        .time-ago {
            color: #7f8c8d;
            font-size: 0.85rem;
        }
        
        .device-info {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            color: #5a6c7d;
        }
        
        .export-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .export-btn:hover {
            background: #5a67d8;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>📧 Email Tracking Dashboard</h1>
            <p>Real-time email analytics and engagement tracking</p>
            <div class="live-indicator">
                <span class="live-dot"></span>
                <span>Live Updates</span>
            </div>
        </div>
    </div>
    
    <div class="container">
        <!-- İstatistik Kartları -->
        <div class="stats-grid">
            <div class="stat-card blue">
                <div class="icon">
                    <i class="fas fa-envelope-open"></i>
                </div>
                <div class="label">Toplam Açılma</div>
                <div class="value">{{ total_opens }}</div>
                <div class="change positive">
                    <i class="fas fa-arrow-up"></i> {{ today_opens }} bugün
                </div>
            </div>
            
            <div class="stat-card green">
                <div class="icon">
                    <i class="fas fa-users"></i>
                </div>
                <div class="label">Benzersiz Açılma</div>
                <div class="value">{{ unique_opens }}</div>
                <div class="change positive">
                    <i class="fas fa-percentage"></i> {{ open_rate }}% oran
                </div>
            </div>
            
            <div class="stat-card orange">
                <div class="icon">
                    <i class="fas fa-mouse-pointer"></i>
                </div>
                <div class="label">Link Tıklamaları</div>
                <div class="value">{{ total_clicks }}</div>
                <div class="change positive">
                    <i class="fas fa-chart-line"></i> {{ click_rate }}% CTR
                </div>
            </div>
            
            <div class="stat-card purple">
                <div class="icon">
                    <i class="fas fa-bolt"></i>
                </div>
                <div class="label">Aktif Kampanyalar</div>
                <div class="value">{{ active_campaigns }}</div>
                <div class="change">
                    <i class="fas fa-clock"></i> Son 7 gün
                </div>
            </div>
        </div>
        
        <!-- Grafikler -->
        <div class="chart-container">
            <h3 style="margin-bottom: 1.5rem;">📊 Son 7 Günlük Aktivite</h3>
            <div style="position: relative; height: 300px;">
                <canvas id="activityChart"></canvas>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
            <div class="chart-container">
                <h3 style="margin-bottom: 1.5rem;">🏆 Top Performing Campaigns</h3>
                <div style="position: relative; height: 250px;">
                    <canvas id="campaignChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container">
                <h3 style="margin-bottom: 1.5rem;">📱 Device Breakdown</h3>
                <div style="position: relative; height: 250px;">
                    <canvas id="deviceChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- En Aktif Emailler -->
        <div class="table-container">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h3>🔥 En Aktif Emailler</h3>
                <button class="export-btn" onclick="exportData()">
                    <i class="fas fa-download"></i> Export CSV
                </button>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Email</th>
                        <th>Açılma</th>
                        <th>Tıklama</th>
                        <th>Engagement Score</th>
                        <th>Son Aktivite</th>
                    </tr>
                </thead>
                <tbody>
                    {% for email in top_emails %}
                    <tr>
                        <td>
                            <a href="/email/{{ email.email }}" class="email-link">{{ email.email }}</a>
                        </td>
                        <td>
                            <span class="badge info">{{ email.opens }}</span>
                        </td>
                        <td>
                            <span class="badge warning">{{ email.clicks }}</span>
                        </td>
                        <td>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <div style="width: 100px; height: 8px; background: #e9ecef; border-radius: 4px;">
                                    <div style="width: {{ email.score }}%; height: 100%; background: #4caf50; border-radius: 4px;"></div>
                                </div>
                                <span>{{ email.score }}%</span>
                            </div>
                        </td>
                        <td class="time-ago">{{ email.last_activity }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <!-- Son Aktiviteler -->
        <div class="table-container">
            <h3 style="margin-bottom: 1.5rem;">⚡ Son Aktiviteler</h3>
            <table>
                <thead>
                    <tr>
                        <th>Zaman</th>
                        <th>Email</th>
                        <th>Kampanya</th>
                        <th>Aktivite</th>
                        <th>Cihaz</th>
                    </tr>
                </thead>
                <tbody>
                    {% for activity in recent_activities %}
                    <tr>
                        <td class="time-ago">{{ activity.time_ago }}</td>
                        <td>
                            <a href="/email/{{ activity.email }}" class="email-link">{{ activity.email }}</a>
                        </td>
                        <td>
                            <span class="badge info">{{ activity.campaign_id[:8] }}...</span>
                        </td>
                        <td>
                            {% if activity.type == 'open' %}
                                <span class="badge success"><i class="fas fa-envelope-open"></i> Açıldı</span>
                            {% else %}
                                <span class="badge warning"><i class="fas fa-mouse-pointer"></i> Tıklandı</span>
                            {% endif %}
                        </td>
                        <td>
                            <div class="device-info">
                                {% if 'Mobile' in activity.device %}
                                    <i class="fas fa-mobile-alt"></i>
                                {% else %}
                                    <i class="fas fa-desktop"></i>
                                {% endif %}
                                {{ activity.device }}
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Activity Chart
        const activityCtx = document.getElementById('activityChart').getContext('2d');
        new Chart(activityCtx, {
            type: 'line',
            data: {
                labels: {{ daily_labels | safe }},
                datasets: [{
                    label: 'Açılmalar',
                    data: {{ daily_opens | safe }},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Tıklamalar',
                    data: {{ daily_clicks | safe }},
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: 10,
                        bottom: 10
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
        
        // Campaign Performance Chart
        const campaignCtx = document.getElementById('campaignChart').getContext('2d');
        new Chart(campaignCtx, {
            type: 'doughnut',
            data: {
                labels: {{ campaign_labels | safe }},
                datasets: [{
                    data: {{ campaign_data | safe }},
                    backgroundColor: [
                        '#667eea',
                        '#f59e0b',
                        '#10b981',
                        '#ef4444',
                        '#8b5cf6'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: 10
                },
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        
        // Device Chart
        const deviceCtx = document.getElementById('deviceChart').getContext('2d');
        new Chart(deviceCtx, {
            type: 'pie',
            data: {
                labels: {{ device_labels | safe }},
                datasets: [{
                    data: {{ device_data | safe }},
                    backgroundColor: [
                        '#3b82f6',
                        '#10b981',
                        '#f59e0b',
                        '#ef4444'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        
        // Auto refresh every 30 seconds
        setTimeout(() => {
            location.reload();
        }, 30000);
        
        // Export function
        function exportData() {
            window.location.href = '/export/csv';
        }
    </script>
</body>
</html>
"""

def init_db():
    """Veritabanı tablolarını oluştur"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Opens tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS opens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            campaign_id TEXT NOT NULL,
            opened_at TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            device_type TEXT,
            browser TEXT,
            os TEXT,
            country TEXT,
            city TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # Clicks tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            campaign_id TEXT NOT NULL,
            link_id TEXT NOT NULL,
            original_url TEXT,
            clicked_at TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            device_type TEXT,
            browser TEXT,
            os TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # Campaign stats tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS campaign_stats (
            campaign_id TEXT PRIMARY KEY,
            total_sent INTEGER DEFAULT 0,
            unique_opens INTEGER DEFAULT 0,
            total_opens INTEGER DEFAULT 0,
            unique_clicks INTEGER DEFAULT 0,
            total_clicks INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # İndeksler
    c.execute("CREATE INDEX IF NOT EXISTS idx_opens_email ON opens(email)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_opens_campaign ON opens(campaign_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_clicks_email ON clicks(email)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_clicks_campaign ON clicks(campaign_id)")
    
    conn.commit()
    conn.close()

def create_pixel():
    """1x1 transparent GIF pixel oluştur"""
    # GIF89a format - 1x1 transparent pixel
    pixel_data = base64.b64decode(
        b'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
    )
    return BytesIO(pixel_data)

def parse_user_agent(ua_string):
    """User agent bilgilerini parse et"""
    try:
        user_agent = user_agents.parse(ua_string)
        
        device_type = "Desktop"
        if user_agent.is_mobile:
            device_type = "Mobile"
        elif user_agent.is_tablet:
            device_type = "Tablet"
        
        return {
            'device_type': device_type,
            'browser': f"{user_agent.browser.family} {user_agent.browser.version_string}",
            'os': f"{user_agent.os.family} {user_agent.os.version_string}"
        }
    except:
        return {
            'device_type': 'Unknown',
            'browser': 'Unknown',
            'os': 'Unknown'
        }

def get_location_from_ip(ip_address):
    """IP adresinden lokasyon bilgisi al (opsiyonel)"""
    # Bu fonksiyon için external API kullanabilirsiniz
    # Örnek: ipapi.co, ipgeolocation.io
    return {
        'country': 'Unknown',
        'city': 'Unknown'
    }

def log_open(email, campaign_id, request):
    """Email açılmasını logla"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # User agent parse et
    ua_info = parse_user_agent(request.headers.get('User-Agent', ''))
    
    # IP lokasyon (opsiyonel)
    location = get_location_from_ip(request.remote_addr)
    
    # Açılmayı kaydet
    now = datetime.datetime.now().isoformat()
    c.execute("""
        INSERT INTO opens 
        (email, campaign_id, opened_at, ip_address, user_agent, device_type, browser, os, country, city)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        email, campaign_id, now,
        request.remote_addr,
        request.headers.get('User-Agent', ''),
        ua_info['device_type'],
        ua_info['browser'],
        ua_info['os'],
        location['country'],
        location['city']
    ))
    
    # Campaign stats güncelle
    update_campaign_stats(c, campaign_id, 'open')
    
    conn.commit()
    conn.close()

def log_click(email, campaign_id, link_id, original_url, request):
    """Link tıklamasını logla"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # User agent parse et
    ua_info = parse_user_agent(request.headers.get('User-Agent', ''))
    
    # Tıklamayı kaydet
    now = datetime.datetime.now().isoformat()
    c.execute("""
        INSERT INTO clicks 
        (email, campaign_id, link_id, original_url, clicked_at, ip_address, user_agent, device_type, browser, os)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        email, campaign_id, link_id, original_url, now,
        request.remote_addr,
        request.headers.get('User-Agent', ''),
        ua_info['device_type'],
        ua_info['browser'],
        ua_info['os']
    ))
    
    # Campaign stats güncelle
    update_campaign_stats(c, campaign_id, 'click')
    
    conn.commit()
    conn.close()

def update_campaign_stats(cursor, campaign_id, action_type):
    """Kampanya istatistiklerini güncelle"""
    if action_type == 'open':
        cursor.execute("""
            UPDATE campaign_stats 
            SET total_opens = total_opens + 1,
                unique_opens = (SELECT COUNT(DISTINCT email) FROM opens WHERE campaign_id = ?),
                updated_at = datetime('now')
            WHERE campaign_id = ?
        """, (campaign_id, campaign_id))
    elif action_type == 'click':
        cursor.execute("""
            UPDATE campaign_stats 
            SET total_clicks = total_clicks + 1,
                unique_clicks = (SELECT COUNT(DISTINCT email) FROM clicks WHERE campaign_id = ?),
                updated_at = datetime('now')
            WHERE campaign_id = ?
        """, (campaign_id, campaign_id))

def calculate_time_ago(timestamp):
    """Zaman farkını hesapla"""
    try:
        dt = datetime.datetime.fromisoformat(timestamp)
        delta = datetime.datetime.now() - dt
        
        if delta.days > 0:
            return f"{delta.days} gün önce"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600} saat önce"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60} dakika önce"
        else:
            return "Az önce"
    except:
        return "Bilinmiyor"

def get_dashboard_data():
    """Dashboard için veri hazırla"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Genel istatistikler
    c.execute("SELECT COUNT(*) FROM opens")
    total_opens = c.fetchone()[0]
    
    c.execute("SELECT COUNT(DISTINCT email) FROM opens")
    unique_opens = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM clicks")
    total_clicks = c.fetchone()[0]
    
    # Bugünkü açılmalar
    today = datetime.datetime.now().date().isoformat()
    c.execute("SELECT COUNT(*) FROM opens WHERE DATE(opened_at) = ?", (today,))
    today_opens = c.fetchone()[0]
    
    # Son 7 gündeki kampanyalar
    week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
    c.execute("SELECT COUNT(DISTINCT campaign_id) FROM opens WHERE opened_at > ?", (week_ago,))
    active_campaigns = c.fetchone()[0]
    
    # Open rate (varsayılan 1000 gönderim üzerinden)
    total_sent = max(10, unique_opens * 2)  # Bu değeri gerçek gönderim sayısından alabilirsiniz
    open_rate = round((unique_opens / total_sent * 100) if total_sent > 0 else 0, 1)
    click_rate = round((total_clicks / total_opens * 100) if total_opens > 0 else 0, 1)
    
    # Son 7 günlük aktivite
    daily_stats = []
    for i in range(6, -1, -1):
        date = (datetime.datetime.now() - datetime.timedelta(days=i)).date()
        c.execute("""
            SELECT 
                (SELECT COUNT(*) FROM opens WHERE DATE(opened_at) = ?) as opens,
                (SELECT COUNT(*) FROM clicks WHERE DATE(clicked_at) = ?) as clicks
        """, (date.isoformat(), date.isoformat()))
        daily_stats.append(c.fetchone())
    
    daily_labels = [(datetime.datetime.now() - datetime.timedelta(days=i)).strftime('%d/%m') for i in range(6, -1, -1)]
    daily_opens = [stat[0] for stat in daily_stats]
    daily_clicks = [stat[1] for stat in daily_stats]
    
    # Top performing campaigns
    c.execute("""
        SELECT campaign_id, COUNT(DISTINCT email) as unique_opens
        FROM opens
        GROUP BY campaign_id
        ORDER BY unique_opens DESC
        LIMIT 5
    """)
    top_campaigns = c.fetchall()
    campaign_labels = [f"Campaign {camp[0][:8]}" for camp in top_campaigns]
    campaign_data = [camp[1] for camp in top_campaigns]
    
    # Device breakdown
    c.execute("""
        SELECT device_type, COUNT(*) as count
        FROM opens
        WHERE device_type IS NOT NULL
        GROUP BY device_type
    """)
    device_stats = c.fetchall()
    device_labels = [dev[0] for dev in device_stats]
    device_data = [dev[1] for dev in device_stats]
    
    # Top emails
    c.execute("""
        SELECT 
            o.email,
            COUNT(DISTINCT o.id) as opens,
            (SELECT COUNT(*) FROM clicks c WHERE c.email = o.email) as clicks,
            MAX(o.opened_at) as last_activity
        FROM opens o
        GROUP BY o.email
        ORDER BY opens DESC
        LIMIT 10
    """)
    top_emails_raw = c.fetchall()
    
    top_emails = []
    for email in top_emails_raw:
        # Engagement score hesapla
        score = min(100, (email[1] * 10 + email[2] * 20))
        top_emails.append({
            'email': email[0],
            'opens': email[1],
            'clicks': email[2],
            'score': score,
            'last_activity': calculate_time_ago(email[3])
        })
    
    # Recent activities
    c.execute("""
        SELECT 
            'open' as type, email, campaign_id, opened_at as timestamp, 
            device_type, browser
        FROM opens
        UNION ALL
        SELECT 
            'click' as type, email, campaign_id, clicked_at as timestamp,
            device_type, browser
        FROM clicks
        ORDER BY timestamp DESC
        LIMIT 20
    """)
    
    activities_raw = c.fetchall()
    recent_activities = []
    for act in activities_raw:
        recent_activities.append({
            'type': act[0],
            'email': act[1],
            'campaign_id': act[2],
            'time_ago': calculate_time_ago(act[3]),
            'device': f"{act[4] or 'Unknown'} - {act[5] or 'Unknown'}"
        })
    
    conn.close()
    
    return {
        'total_opens': total_opens,
        'unique_opens': unique_opens,
        'total_clicks': total_clicks,
        'today_opens': today_opens,
        'active_campaigns': active_campaigns,
        'open_rate': open_rate,
        'click_rate': click_rate,
        'daily_labels': json.dumps(daily_labels),
        'daily_opens': json.dumps(daily_opens),
        'daily_clicks': json.dumps(daily_clicks),
        'campaign_labels': json.dumps(campaign_labels),
        'campaign_data': json.dumps(campaign_data),
        'device_labels': json.dumps(device_labels),
        'device_data': json.dumps(device_data),
        'top_emails': top_emails,
        'recent_activities': recent_activities
    }

# Routes
@app.route("/")
def dashboard():
    """Ana dashboard"""
    data = get_dashboard_data()
    return render_template_string(DASHBOARD_TEMPLATE, **data)

@app.route("/open", methods=["GET"])
def track_open():
    """Email açılma takibi"""
    email = request.args.get("email")
    campaign_id = request.args.get("cid")
    
    if email and campaign_id:
        log_open(email, campaign_id, request)
    
    # 1x1 transparent pixel döndür
    return send_file(create_pixel(), mimetype="image/gif")

@app.route("/click/<link_id>")
def track_click(link_id):
    """Link tıklama takibi"""
    email = request.args.get("email")
    campaign_id = request.args.get("cid")
    url = request.args.get("url")
    
    if email and campaign_id and url:
        log_click(email, campaign_id, link_id, url, request)
    
    # Orijinal URL'e yönlendir
    return redirect(url or "https://example.com")

@app.route("/api/stats")
def api_stats():
    """JSON API endpoint"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Genel istatistikler
    c.execute("""
        SELECT 
            (SELECT COUNT(*) FROM opens) as total_opens,
            (SELECT COUNT(DISTINCT email) FROM opens) as unique_opens,
            (SELECT COUNT(*) FROM clicks) as total_clicks,
            (SELECT COUNT(DISTINCT email) FROM clicks) as unique_clicks
    """)
    general_stats = c.fetchone()
    
    # Email başına detaylar
    c.execute("""
        SELECT 
            o.email,
            COUNT(DISTINCT o.id) as open_count,
            (SELECT COUNT(*) FROM clicks c WHERE c.email = o.email) as click_count,
            MIN(o.opened_at) as first_open,
            MAX(o.opened_at) as last_open
        FROM opens o
        GROUP BY o.email
    """)
    email_details = []
    for row in c.fetchall():
        email_details.append({
            'email': row[0],
            'opens': row[1],
            'clicks': row[2],
            'first_open': row[3],
            'last_open': row[4],
            'engagement_score': min(100, row[1] * 10 + row[2] * 20)
        })
    
    # Kampanya performansı
    c.execute("""
        SELECT 
            campaign_id,
            COUNT(DISTINCT email) as unique_opens,
            COUNT(*) as total_opens,
            (SELECT COUNT(DISTINCT email) FROM clicks WHERE campaign_id = o.campaign_id) as unique_clicks,
            (SELECT COUNT(*) FROM clicks WHERE campaign_id = o.campaign_id) as total_clicks,
            MIN(opened_at) as first_open,
            MAX(opened_at) as last_open
        FROM opens o
        GROUP BY campaign_id
    """)
    campaign_performance = []
    for row in c.fetchall():
        campaign_performance.append({
            'campaign_id': row[0],
            'unique_opens': row[1],
            'total_opens': row[2],
            'unique_clicks': row[3],
            'total_clicks': row[4],
            'first_open': row[5],
            'last_open': row[6],
            'open_rate': 0,  # Gerçek gönderim sayısı ile hesaplanmalı
            'click_rate': round((row[3] / row[1] * 100) if row[1] > 0 else 0, 2)
        })
    
    conn.close()
    
    return jsonify({
        'general_stats': {
            'total_opens': general_stats[0],
            'unique_opens': general_stats[1],
            'total_clicks': general_stats[2],
            'unique_clicks': general_stats[3]
        },
        'email_details': email_details,
        'campaign_performance': campaign_performance,
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route("/email/<email>")
def email_detail(email):
    """Tek bir email için detaylı rapor"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Email aktiviteleri
    c.execute("""
        SELECT 
            'open' as type, campaign_id, opened_at as timestamp, 
            device_type, browser, os, ip_address
        FROM opens WHERE email = ?
        UNION ALL
        SELECT 
            'click' as type, campaign_id, clicked_at as timestamp,
            device_type, browser, os, ip_address
        FROM clicks WHERE email = ?
        ORDER BY timestamp DESC
    """, (email, email))
    
    activities = c.fetchall()
    conn.close()
    
    # Simple detail page
    html = f"""
    <html>
    <head>
        <title>Email Detail: {email}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
        </style>
    </head>
    <body>
        <h1>Email Detail: {email}</h1>
        <h2>Activity History</h2>
        <table>
            <tr>
                <th>Type</th>
                <th>Campaign</th>
                <th>Time</th>
                <th>Device</th>
                <th>Browser</th>
                <th>OS</th>
                <th>IP</th>
            </tr>
    """
    
    for act in activities:
        html += f"""
            <tr>
                <td>{'📧 Open' if act[0] == 'open' else '🔗 Click'}</td>
                <td>{act[1]}</td>
                <td>{act[2]}</td>
                <td>{act[3] or 'Unknown'}</td>
                <td>{act[4] or 'Unknown'}</td>
                <td>{act[5] or 'Unknown'}</td>
                <td>{act[6]}</td>
            </tr>
        """
    
    html += """
        </table>
        <br>
        <a href="/">← Back to Dashboard</a>
    </body>
    </html>
    """
    
    return html

@app.route("/export/csv")
def export_csv():
    """CSV export"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Email bazlı özet rapor
    c.execute("""
        SELECT 
            o.email,
            COUNT(DISTINCT o.id) as opens,
            (SELECT COUNT(*) FROM clicks c WHERE c.email = o.email) as clicks,
            MIN(o.opened_at) as first_open,
            MAX(o.opened_at) as last_open
        FROM opens o
        GROUP BY o.email
        ORDER BY opens DESC
    """)
    
    # CSV oluştur
    csv_data = "Email,Opens,Clicks,First Open,Last Open,Engagement Score\n"
    for row in c.fetchall():
        score = min(100, row[1] * 10 + row[2] * 20)
        csv_data += f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{score}\n"
    
    conn.close()
    
    # CSV olarak gönder
    response = app.response_class(
        response=csv_data,
        status=200,
        mimetype='text/csv'
    )
    response.headers["Content-Disposition"] = f"attachment; filename=email_tracking_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return response

@app.route("/campaign/<campaign_id>")
def campaign_detail(campaign_id):
    """Kampanya detay sayfası"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Kampanya özeti
    c.execute("""
        SELECT 
            COUNT(DISTINCT email) as unique_opens,
            COUNT(*) as total_opens,
            MIN(opened_at) as first_open,
            MAX(opened_at) as last_open
        FROM opens 
        WHERE campaign_id = ?
    """, (campaign_id,))
    
    stats = c.fetchone()
    
    # Email listesi
    c.execute("""
        SELECT 
            email,
            COUNT(*) as open_count,
            MAX(opened_at) as last_open
        FROM opens
        WHERE campaign_id = ?
        GROUP BY email
        ORDER BY open_count DESC
    """, (campaign_id,))
    
    emails = c.fetchall()
    conn.close()
    
    html = f"""
    <html>
    <head>
        <title>Campaign: {campaign_id}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .stat {{ display: inline-block; margin: 10px; padding: 10px; background: #f0f0f0; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
        </style>
    </head>
    <body>
        <h1>Campaign: {campaign_id}</h1>
        
        <div class="stat">
            <strong>Unique Opens:</strong> {stats[0]}
        </div>
        <div class="stat">
            <strong>Total Opens:</strong> {stats[1]}
        </div>
        <div class="stat">
            <strong>First Open:</strong> {stats[2]}
        </div>
        <div class="stat">
            <strong>Last Open:</strong> {stats[3]}
        </div>
        
        <h2>Email Engagement</h2>
        <table>
            <tr>
                <th>Email</th>
                <th>Opens</th>
                <th>Last Open</th>
            </tr>
    """
    
    for email in emails:
        html += f"""
            <tr>
                <td><a href="/email/{email[0]}">{email[0]}</a></td>
                <td>{email[1]}</td>
                <td>{email[2]}</td>
            </tr>
        """
    
    html += """
        </table>
        <br>
        <a href="/">← Back to Dashboard</a>
    </body>
    </html>
    """
    
    return html

if __name__ == "__main__":
    # Veritabanını başlat
    init_db()
    
    # Sunucuyu başlat
    print("🚀 Email Tracking Server başlatılıyor...")
    print("📊 Dashboard: http://0.0.0.0:8080")
    print("📧 Tracking Pixel: http://0.0.0.0:8080/open?email=EMAIL&cid=CAMPAIGN_ID")
    print("🔗 Link Tracking: http://0.0.0.0:8080/click/LINK_ID?email=EMAIL&cid=CAMPAIGN_ID&url=TARGET_URL")
    print("📡 API Endpoint: http://0.0.0.0:8080/api/stats")
    
    app.run(host="0.0.0.0", port=8080, debug=False)