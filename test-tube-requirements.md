# Test Tube Project - Setup Guide

## 📋 Requirements Files

### requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
solana==0.30.2
solders==0.18.1
qrcode[pil]==7.4.2
openai==1.3.0
pandas==2.1.3
python-multipart==0.0.6
streamlit==1.29.0
requests==2.31.0
plotly==5.18.0
pillow==10.1.0
```

### .env (Create this file - DO NOT commit to git)
```
OPENAI_API_KEY=your-openai-api-key-here
SOLANA_RPC_URL=https://api.devnet.solana.com
```

## 🚀 Quick Start

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/your-username/test-tube-project.git
cd test-tube-project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Create .env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# Get one from: https://platform.openai.com/api-keys
```

### 3. Run the Application

#### Terminal 1 - Start Backend API:
```bash
python main.py
# API will run on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

#### Terminal 2 - Start Dashboard:
```bash
streamlit run dashboard.py
# Dashboard will open at http://localhost:8501
```

## 🏗️ Project Structure
```
test-tube-project/
│
├── main.py                 # FastAPI backend
├── dashboard.py            # Dashboard UI built with streamlit
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (create this)
├── payer.json            # Auto-generated wallet (don't share!)
├── transactions.json     # Transaction database
└── README.md            # Project documentation
```

## 🔑 Key Features Implemented

### ✅ Core Features
- **Solana Pay Integration**: Send/receive SOL payments on devnet
- **QR Code Generation**: Solana Pay QR codes for merchants
- **Transaction Tracking**: Complete history with categorization
- **Multi-currency Display**: SOL and Naira (₦) amounts

### 🤖 AI Features
- **Natural Language Insights**: Plain English spending analysis
- **Smart Recommendations**: Personalized saving tips
- **Spending Patterns**: AI-detected unusual activity
- **Budget Predictions**: Future spending projections

### 📊 Analytics
- **Real-time Dashboard**: Live spending metrics
- **Category Breakdown**: Visual spending distribution
- **Time Analysis**: Hour/day patterns
- **Export to Excel**: CSV download for reports
- **Merchant Analytics**: Top vendors tracking

### 🎓 Student-Focused
- **Campus Categories**: Food, transport, data, books
- **Merchant Directory**: Registered campus vendors
- **Simple Interface**: No crypto jargon
- **Mobile-Friendly**: Responsive design

## 💡 Testing the System

### 1. Get Test SOL (Devnet)
The system automatically requests airdrops when balance is low.

### 2. Sample Test Addresses (For Testing)
```
Campus Cafeteria: 11111111111111111111111111111111
Transport Service: 22222222222222222222222222222222
Data Reseller: 33333333333333333333333333333333
Bookstore: 44444444444444444444444444444444
```

### 3. Test Workflow
1. Open dashboard (http://localhost:8501)
2. Go to "Make Payment"
3. Select a merchant or enter custom address
4. Enter amount (try 0.01 SOL)
5. Submit payment
6. Check Dashboard for analytics
7. View AI Insights for spending advice

## 🔄 Next Steps for Production

### 1. Blockchain Integration
- [ ] Switch from devnet to mainnet-beta
- [ ] Integrate cNGN stablecoin
- [ ] Implement proper wallet management
- [ ] Add transaction confirmation checks

### 2. Security Enhancements
- [ ] Implement proper authentication
- [ ] Secure private key management
- [ ] Add rate limiting
- [ ] Implement input validation
- [ ] Add CORS configuration

### 3. Database
- [ ] Replace JSON with PostgreSQL
- [ ] Add user accounts system
- [ ] Implement proper data models
- [ ] Add backup mechanisms

### 4. AI Improvements
- [ ] Fine-tune AI model for Nigerian context
- [ ] Add voice input/output
- [ ] Implement predictive analytics
- [ ] Add fraud detection

### 5. Mobile App
- [ ] React Native mobile app
- [ ] Push notifications
- [ ] Biometric authentication
- [ ] Offline transaction queueing

### 6. Campus Integration
- [ ] Create wide-spread awareness
- [ ] Onboard real merchants
- [ ] Integration with school portals

## 🐛 Troubleshooting

### Common Issues:

**1. "Connection refused" error**
- Ensure backend is running on port 8000
- Check firewall settings

**2. "Invalid recipient address"**
- Use valid base58 Solana addresses
- Test with provided sample addresses

**3. "Insufficient balance"**
- Wait for automatic airdrop (devnet only)
- Check RPC connection

**4. AI insights not working**
- Verify OpenAI API key in .env
- Check API rate limits

## 📚 Resources

- [Solana Documentation](https://docs.solana.com)
- [Solana Pay Spec](https://docs.solanapay.com)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Streamlit Docs](https://docs.streamlit.io)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request
6. Reach out via email: samidope15@gmail.com or "samuelachilike." on discord

## 🙏 Acknowledgments

- Solana Students Africa
- Claude AI
- And ofcourse the Lord Almighty

---

**Built with ❤️ for African Students**

*Making Web3 infrastructure accessible to African Students, one campus at a time* 🧪