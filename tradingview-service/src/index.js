require('dotenv').config(); // Load environment variables at the top

const WebSocket = require('ws');
const { createLogger, format, transports } = require('winston');
const TradingView = require('@mathieuc/tradingview');

// Logger Configuration
const logger = createLogger({
    level: 'info',
    format: format.combine(
        format.timestamp(),
        format.errors({ stack: true }),
        format.splat(),
        format.json()
    ),
    defaultMeta: { service: 'tradingview-data-service' },
    transports: [
        new transports.Console({
            format: format.simple()
        }),
        new transports.File({ filename: 'error.log', level: 'error' }),
        new transports.File({ filename: 'combined.log' })
    ]
});

// TradingView WebSocket Server Configuration
const PORT = process.env.PORT || 8765;
const wss = new WebSocket.Server({ port: PORT });

// Log environment variables for debugging
console.log('Environment Variables:', {
    USERNAME: process.env.TRADINGVIEW_USERNAME ? 'PRESENT' : 'MISSING',
    PASSWORD: process.env.TRADINGVIEW_PASSWORD ? 'PRESENT' : 'MISSING'
});

// Login credentials from environment variables
const USERNAME = process.env.TRADINGVIEW_USERNAME;
const PASSWORD = process.env.TRADINGVIEW_PASSWORD;

// Global authenticated client
let authenticatedClient = null;

// Login function with detailed logging
async function loginToTradingView() {
    try {
        if (!USERNAME || !PASSWORD) {
            console.error('Detailed Environment Check:', {
                USERNAME_TYPE: typeof USERNAME,
                USERNAME_VALUE: USERNAME,
                PASSWORD_TYPE: typeof PASSWORD,
                PASSWORD_VALUE: PASSWORD ? '[REDACTED]' : undefined
            });
            throw new Error('TradingView username or password not provided');
        }

        logger.info('Attempting login...');

        return new Promise((resolve, reject) => {
            const client = new TradingView.Client({
                log: true
            });

            client.login(USERNAME, PASSWORD)
                .then(() => {
                    logger.info('Successfully logged in');
                    authenticatedClient = client;
                    resolve(client);
                })
                .catch((error) => {
                    logger.error('Login failed:', error);
                    reject(error);
                });
        });
    } catch (error) {
        logger.error('TradingView Login Error:', error);
        throw error;
    }
}

// Initial login attempt
(async () => {
    logger.info('Starting login process...');
    try {
        await loginToTradingView();
        logger.info('Login process completed successfully');
    } catch (err) {
        logger.error('Initial login failed:', err);
    }
})();

logger.info(`TradingView WebSocket server running on port ${PORT}`);

// WebSocket server logic continues...
module.exports = { loginToTradingView };
