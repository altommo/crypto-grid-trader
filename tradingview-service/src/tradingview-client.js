const TradingView = require('@mathieuc/tradingview');
const { handleCaptchaLogin } = require('./auth');

class TradingViewClient {
    constructor(username, password) {
        this.username = username;
        this.password = password;
        this.client = null;
    }

    async login() {
        try {
            console.log('Attempting TradingView login...');
            
            // First, try standard login
            try {
                this.client = new TradingView.Client({ log: true });
                await this.client.login(this.username, this.password);
                console.log('Standard login successful');
                return this.client;
            } catch (standardLoginError) {
                console.log('Standard login failed, attempting CAPTCHA login...');
                
                // If standard login fails, use CAPTCHA fallback
                const credentials = await handleCaptchaLogin(this.username, this.password);
                
                this.client = new TradingView.Client({
                    token: credentials.session,
                    signature: credentials.signature
                });
                
                console.log('CAPTCHA login successful');
                return this.client;
            }
        } catch (error) {
            console.error('TradingView login failed:', error);
            throw error;
        }
    }

    async getChartData(symbol, interval, range = 100) {
        if (!this.client) {
            await this.login();
        }

        return new Promise((resolve, reject) => {
            const chart = new this.client.Session.Chart();
            
            chart.setMarket(symbol, {
                timeframe: interval,
                range: range,
                to: Math.floor(Date.now() / 1000)
            }, () => {
                // Resolve with raw chart data
                resolve({
                    periods: chart.periods || [],
                    symbol: symbol,
                    interval: interval
                });
            });
        });
    }
}

module.exports = TradingViewClient;
