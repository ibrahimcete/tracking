from flask import Flask, request, send_file, jsonify, render_template_string
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from io import BytesIO
import json

app = Flask(__name__)

# Database bağlantısı
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    """Database bağlantısı al"""
    if DATABASE_URL:
        # Render SSL fix
        db_url = DATABASE_URL.replace('postgres://', 'postgresql://')
        return psycopg2.connect(db_url, sslmode='require')
    return None

def init_db():
    """Tabloları oluştur"""
    conn = get_db()
    if not conn:
        print("Database bağlantısı yok!")
        return
        
    cur = conn.cursor()
    
    # Opens tablosu
    cur.execute("""
        CREATE TABLE IF NOT EXISTS opens (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            campaign VARCHAR(255) NOT NULL,
            opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address VARCHAR(50),
            user_agent TEXT
        )
    """)
    
    # İndeks ekle (hızlı sorgular için)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_opens_email ON opens(email);
        CREATE INDEX IF NOT EXISTS idx_opens_campaign ON opens(campaign);
        CREATE INDEX IF NOT EXISTS idx_opens_date ON opens(opened_at);
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database tabloları hazır!")

# Uygulama başlarken
init_db()

# Modern Dashboard HTML (öncekiyle aynı)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📧 Email Analytics - PostgreSQL</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
        }
        
        .header h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .db-status {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: #10b981;
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
            margin-left: 20px;
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
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 15px 0 5px 0;
        }
        
        .stat-label {
            color: #6b7280;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .table-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 30px;
            margin-top: 30px;
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
        
        .pulse {
            width: 8px;
            height: 8px;
            background: white;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="display: flex; align-items: center;">
                <h1>📧 Email Analytics Dashboard</h1>
                <div class="db-status">
                    <div class="pulse"></div>
                    <span>PostgreSQL Aktif</span>
                </div>
            </div>
            <p style="color: #6b7280; margin-top: 10px;">
                Veriler artık kalıcı! Server restart olsa bile kaybolmaz 🎉
            </p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <i class="fas fa-envelope-open" style="font-size: 2rem; color: #667eea;"></i>
                <div class="stat-value">{{ total_opens }}</div>
                <div class="stat-label">Toplam Açılma</div>
            </div>
            
            <div class="stat-card">
                <i class="fas fa-users" style="font-size: 2rem; color: #10b981;"></i>
                <div class="stat-value">{{ unique_opens }}</div>
                <div class="stat-label">Benzersiz Email</div>
            </div>
            
            <div class="stat-card">
                <i class="fas fa-clock" style="font-size: 2rem; color: #fb923c;"></i>
                <div class="stat-value">{{ today_opens }}</div>
                <div class="stat-label">Bugünkü Açılmalar</div>
            </div>
            
            <div class="stat-card">
                <i class="fas fa-percentage" style="font-size: 2rem; color: #ef4444;"></i>
                <div class="stat-value">{{ open_rate }}%</div>
                <div class="stat-label">Açılma Oranı</div>
            </div>
        </div>
        
        <div class="table-container">
            <h3 style="margin-bottom: 20px;">⚡ Son Aktiviteler</h3>
            <table>
                <thead>
                    <tr>
                        <th>Email</th>
                        <th>Kampanya</th>
                        <th>Zaman</th>
                        <th>IP Adresi</th>
                    </tr>
                </thead>
                <tbody>
                    {% for activity in recent_activities %}
                    <tr>
                        <td>{{ activity.email }}</td>
                        <td><span class="badge">{{ activity.campaign }}</span></td>
                        <td>{{ activity.time_ago }}</td>
                        <td style="color: #6b7280;">{{ activity.ip_address }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    """Dashboard - PostgreSQL'den veri çek"""
    conn = get_db()
    if not conn:
        return "Database bağlantısı yok!"
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # İstatistikler
    cur.execute("SELECT COUNT(*) as total FROM opens")
    total_opens = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(DISTINCT email) as unique FROM opens")
    unique_opens = cur.fetchone()['unique']
    
    # Bugünkü
    cur.execute("""
        SELECT COUNT(*) as today 
        FROM opens 
        WHERE DATE(opened_at) = CURRENT_DATE
    """)
    today_opens = cur.fetchone()['today']
    
    # Son 20 aktivite
    cur.execute("""
        SELECT email, campaign, opened_at, ip_address
        FROM opens 
        ORDER BY opened_at DESC 
        LIMIT 20
    """)
    activities = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Zaman hesapla
    recent_activities = []
    for act in activities:
        time_diff = datetime.now() - act['opened_at']
        if time_diff.days > 0:
            time_ago = f"{time_diff.days} gün önce"
        elif time_diff.seconds > 3600:
            time_ago = f"{time_diff.seconds // 3600} saat önce"
        elif time_diff.seconds > 60:
            time_ago = f"{time_diff.seconds // 60} dakika önce"
        else:
            time_ago = "Az önce"
        
        recent_activities.append({
            'email': act['email'],
            'campaign': act['campaign'],
            'time_ago': time_ago,
            'ip_address': act['ip_address'] or 'Bilinmiyor'
        })
    
    # Açılma oranı
    open_rate = round((unique_opens / max(total_opens, 1)) * 100, 1)
    
    return render_template_string(DASHBOARD_HTML,
        total_opens=total_opens,
        unique_opens=unique_opens,
        today_opens=today_opens,
        open_rate=open_rate,
        recent_activities=recent_activities
    )

@app.route("/open")
def track_open():
    """Email açılmasını kaydet - PostgreSQL'e"""
    email = request.args.get("email", "unknown")
    campaign = request.args.get("cid", "unknown")
    
    conn = get_db()
    if conn:
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO opens (email, campaign, ip_address, user_agent)
            VALUES (%s, %s, %s, %s)
        """, (
            email, 
            campaign, 
            request.remote_addr,
            request.headers.get('User-Agent', '')[:500]  # Max 500 karakter
        ))
        
        conn.commit()
        cur.close()
        conn.close()
    
    # 1x1 GIF pixel
    gif_data = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    return send_file(BytesIO(gif_data), mimetype='image/gif')

@app.route("/api/stats")
def api_stats():
    """JSON API - DB'den"""
    conn = get_db()
    if not conn:
        return jsonify({"error": "No database"})
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Genel stats
    cur.execute("""
        SELECT 
            COUNT(*) as total_opens,
            COUNT(DISTINCT email) as unique_emails,
            COUNT(DISTINCT campaign) as total_campaigns
        FROM opens
    """)
    stats = cur.fetchone()
    
    # Son 10
    cur.execute("""
        SELECT email, campaign, opened_at
        FROM opens 
        ORDER BY opened_at DESC 
        LIMIT 10
    """)
    recent = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify({
        'stats': stats,
        'recent': recent
    })

@app.route("/cleanup")
def cleanup():
    """30 günden eski verileri temizle (opsiyonel)"""
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM opens 
            WHERE opened_at < CURRENT_DATE - INTERVAL '30 days'
        """)
        deleted = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        return f"Temizlendi: {deleted} kayıt silindi"
    return "Database yok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
