require('dotenv').config(); // Load environment variables at the top

const WebSocket = require('ws');
const { createLogger, format, transports } = require('winston');
const { handleCaptchaLogin } = require('./auth');
const TradingView = require('tradingview-api'); // Make sure this is imported

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

// Logging the environment variables for debugging
console.log('Environment Variables:', {
    USERNAME: process.env.TRADINGVIEW_USERNAME,
    PASSWORD_LENGTH: process.env.TRADINGVIEW_PASSWORD?.length
});

// Login credentials from environment variables
const USERNAME = process.env.TRADINGVIEW_USERNAME;
const PASSWORD = process.env.TRADINGVIEW_PASSWORD;

// Global authenticated client
let authenticatedClient = null;

// Login function with CAPTCHA fallback
async function loginToTradingView() {
    try {
        if (!USERNAME || !PASSWORD) {
            console.error('Username or Password missing:', { USERNAME, PASSWORD_LENGTH: PASSWORD?.length });
            throw new Error('TradingView username or password not provided');
        }

        logger.info('Attempting login...');

        try {
            // First try normal login
            logger.info('Attempting normal login...');
            const user = await TradingView.loginUser(USERNAME, PASSWORD, false);
            logger.info('Successfully logged in through normal method');
            
            // Create client with authenticated session
            authenticatedClient = new TradingView.Client({
                token: user.session,
                signature: user.sessionid_sign // Updated to match new cookie name
            });

            return authenticatedClient;
        } catch (error) {
            logger.info('Normal login failed with error:', error.message);
            
            // Check if error is CAPTCHA related
            if (error.message.toLowerCase().includes('captcha') || 
                error.message.toLowerCase().includes('robot')) {
                logger.info('CAPTCHA detected, falling back to browser login...');
                
                try {
                    const credentials = await handleCaptchaLogin(USERNAME, PASSWORD);
                    logger.info('Successfully logged in through browser after CAPTCHA');
                    
                    // Create client with authenticated session
                    authenticatedClient = new TradingView.Client({
                        token: credentials.session,
                        signature: credentials.signature
                    });

                    return authenticatedClient;
                } catch (captchaError) {
                    logger.error('CAPTCHA login failed:', captchaError);
                    throw captchaError;
                }
            }
            // If it's not a CAPTCHA error, throw it
            throw error;
        }
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
