import os
import requests
from config import settings

# Mock Data (in practice, load this from your actual source)
data = {
  "farmer": {
    "name": "Ramesh Kumar"
  },
  "stats": {
    "activePolicies": 1,
    "totalPremiumAmount": 0,
    "totalAmountInsured": 16000
  },
  "weatherAlerts": [
    {
      "type": "Heavy Rainfall",
      "date": "2025-05-15",
      "location": "Northern Region",
      "impact": "Moderate"
    },
    {
      "type": "Heatwave",
      "date": "2025-05-18",
      "location": "All Regions",
      "impact": "High"
    }
  ],
  "recentTransactions": [
    {
      "transactionId": "TXN-001",
      "type": "Premium Payment",
      "amount": 1600,
      "date": "2025-04-15",
      "status": "Paid"
    }
  ]
}

# Email body HTML
email_body = f"""
<html>
  <head>
    <style>
      body {{
        font-family: Arial, sans-serif;
        background-color: #f6f9fc;
        color: #333;
        padding: 20px;
      }}
      .card {{
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
      }}
      .title {{
        font-size: 24px;
        color: #007BFF;
        margin-bottom: 10px;
      }}
      .subtitle {{
        font-size: 18px;
        margin-bottom: 10px;
      }}
      .alert {{
        padding: 10px;
        border-left: 5px solid #FF4136;
        margin-bottom: 10px;
        background-color: #ffecec;
        border-radius: 5px;
      }}
      .footer {{
        font-size: 12px;
        color: #999;
        margin-top: 20px;
      }}
    </style>
  </head>
  <body>
    <div class="card">
      <div class="title">Hello {data['farmer']['name']},</div>
      <div class="subtitle">Here’s your latest farming update:</div>

      <div><strong>Active Policies:</strong> {data['stats']['activePolicies']}</div>
      <div><strong>Total Insured:</strong> ₹{data['stats']['totalAmountInsured']}</div>

      <h3 style="margin-top:20px;">Weather Alerts:</h3>
      {"".join(f'''
      <div class="alert">
        <strong>{alert['type']}</strong> expected on <strong>{alert['date']}</strong> in <strong>{alert['location']}</strong>.<br/>
        <em>Impact Level:</em> {alert['impact']}
      </div>
      ''' for alert in data['weatherAlerts'])}

      <h3 style="margin-top:20px;">Recent Transaction:</h3>
      {"".join(f'''
      <div class="card" style="background-color:#f1f1f1;">
        <strong>{txn['type']}</strong><br/>
        Amount: ₹{txn['amount']}<br/>
        Date: {txn['date']}<br/>
        Status: {txn['status']}
      </div>
      ''' for txn in data['recentTransactions'])}

      <div class="footer">
        Stay safe and keep growing!<br/>
        — Your AgriProtect Team
      </div>
    </div>
  </body>
</html>
"""

# Send Mail via Mailjet API
def send_email(to_email, to_name):
    url = "https://api.mailjet.com/v3.1/send"
    headers = {'Content-Type': 'application/json'}
    payload = {
        'Messages': [
            {
                "From": {
                    "Email": "urbnexus@gmail.com",
                    "Name": "AgriProtect"
                },
                "To": [
                    {
                        "Email": to_email,
                        "Name": to_name
                    }
                ],
                "Subject": "Important Weather Alerts & Farming Update",
                "HTMLPart": email_body
            }
        ]
    }

    response = requests.post(
        url,
        auth=(MAILJET_API_KEY, MAILJET_API_SECRET),
        headers=headers,
        json=payload
    )

    print("Response Status:", response.status_code)
    print("Response Body:", response.text)

# Example call
send_email("asghus117@gmail.com", data['farmer']['name'])