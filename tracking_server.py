from flask import Flask, request, send_file, jsonify
import os
from io import BytesIO
from datetime import datetime

app = Flask(__name__)

# Basit memory storage
email_opens = []

@app.route("/")
def home():
    """Dashboard"""
    total = len(email_opens)
    unique = len(set([x['email'] for x in email_opens]))
    
    return f"""
    <html>
    <head>
        <title>Email Tracking</title>
        <style>
            body {{ 
                font-family: Arial; 
                max-width: 800px; 
                margin: 50px auto; 
                padding: 20px;
                background: #f5f5f5;
            }}
            .box {{ 
                background: white; 
                padding: 30px; 
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #333; }}
            .stat {{ 
                display: inline-block; 
                margin: 20px;
                text-align: center;
            }}
            .number {{ 
                font-size: 48px; 
                color: #4CAF50;
                font-weight: bold;
            }}
            .label {{ 
                color: #666;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="box">
            <h1>📧 Email Tracking Dashboard</h1>
            <div class="stat">
                <div class="number">{total}</div>
                <div class="label">Toplam Açılma</div>
            </div>
            <div class="stat">
                <div class="number">{unique}</div>
                <div class="label">Benzersiz Email</div>
            </div>
            <hr>
            <p>API: <a href="/api/stats">/api/stats</a></p>
        </div>
    </body>
    </html>
    """

@app.route("/open")
def track_open():
    """Email açıldığında"""
    email = request.args.get("email", "unknown")
    campaign = request.args.get("cid", "unknown")
    
    # Kaydet
    email_opens.append({
        "email": email,
        "campaign": campaign,
        "time": datetime.now().isoformat(),
        "ip": request.remote_addr
    })
    
    # 1x1 GIF pixel (base64)
    gif_data = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    
    return send_file(BytesIO(gif_data), mimetype='image/gif')

@app.route("/api/stats")
def stats():
    """JSON stats"""
    return jsonify({
        "total_opens": len(email_opens),
        "unique_emails": len(set([x['email'] for x in email_opens])),
        "last_10": email_opens[-10:][::-1]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
