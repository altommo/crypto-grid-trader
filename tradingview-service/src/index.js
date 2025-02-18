require('dotenv').config();
const TradingView = require('@mathieuc/tradingview');
const WebSocket = require('ws');
const { createLogger, format, transports } = require('winston');
const { handleCaptchaLogin } = require('./auth');

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

async function setupIndicators(chart) {
  return new Promise((resolve) => {
    // Add studies to the chart
    const studies = [
      // RSI Study
      chart.addSeries('rsi', {
        length: 14,
        source: 'close'
      }),
      // Bollinger Bands Study
      chart.addSeries('bb', {
        length: 20,
        stdDev: 2,
        source: 'close'
      }),
      // SuperTrend Study
      chart.addPineStudy('PUB;5d17f3008c8e4b4f9af10a8b3c7d27ad', {
        factor: 3,
        period: 10,
        source: 'close'
      })
    ];

    // Wait for data to load
    setTimeout(() => {
      resolve(studies);
    }, 2000);
  });
}

async function getChartData(client, symbol, interval) {
  try {
    logger.info(`Getting chart data for ${symbol} at ${interval} interval`);
    
    // Create chart session
    const chart = new client.Session.Chart();
    
    // Set market and wait for data
    return new Promise((resolve) => {
      chart.setMarket(symbol, {
        timeframe: interval,
        range: 100,
        to: Math.floor(Date.now() / 1000)
      }, async () => {
        // After market is set, add indicators
        const studies = await setupIndicators(chart);
        
        // Prepare data response
        const data = {
          type: 'market_update',
          symbol: symbol,
          interval: interval,
          timestamp: new Date().toISOString(),
          prices: chart.periods || [],
          indicators: {
            RSI: studies[0]?.data || [],
            BB: studies[1]?.data || [],
            SuperTrend: studies[2]?.data || []
          }
        };

        logger.info(`Successfully gathered data for ${symbol}`, {
          hasPrices: (chart.periods || []).length > 0,
          hasIndicators: studies.length
        });

        // Cleanup
        if (chart && typeof chart.delete === 'function') {
          chart.delete();
        }

        resolve(data);
      });
    });
  } catch (error) {
    logger.error(`Error getting chart data for ${symbol}:`, error);
    throw error;
  }
}

// Login credentials from environment variables
const USERNAME = process.env.TRADINGVIEW_USERNAME;
const PASSWORD = process.env.TRADINGVIEW_PASSWORD;

// Global authenticated client
let authenticatedClient = null;

// Login function with CAPTCHA fallback
async function loginToTradingView() {
    try {
        if (!USERNAME || !PASSWORD) {
            console.log('Username and Password:', { 
                USERNAME: USERNAME ? 'PRESENT' : 'MISSING', 
                PASSWORD: PASSWORD ? 'PRESENT' : 'MISSING' 
            });
            throw new Error('TradingView username or password not provided');
        }

        try {
            // First try normal login
            logger.info('Attempting normal login...');
            const user = await TradingView.loginUser(USERNAME, PASSWORD, false);
            logger.info('Successfully logged in through normal method');
            
            // Create client with authenticated session
            authenticatedClient = new TradingView.Client({
                token: user.session,
                signature: user.sessionid_sign // Updated to use sessionid_sign
            });

            return authenticatedClient;
        } catch (error) {
            // Check if error is CAPTCHA related
            if (error.message.toLowerCase().includes('captcha') || 
                error.message.toLowerCase().includes('robot')) {
                logger.info('CAPTCHA detected, falling back to browser login...');
                const credentials = await handleCaptchaLogin(USERNAME, PASSWORD);
                logger.info('Successfully logged in through browser after CAPTCHA');
                
                // Create client with authenticated session
                authenticatedClient = new TradingView.Client({
                    token: credentials.session,
                    signature: credentials.signature
                });

                return authenticatedClient;
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
loginToTradingView().catch(err => {
  logger.error('Initial login failed:', err);
});

logger.info(`TradingView WebSocket server running on port ${PORT}`);

wss.on('connection', (ws) => {
  logger.info('New client connected to TradingView data service');

  ws.on('message', async (rawMessage) => {
    try {
      const message = JSON.parse(rawMessage);
      const { type, symbol, interval } = message;

      logger.info(`Received request: ${JSON.stringify(message)}`);

      // Ensure client is authenticated
      if (!authenticatedClient) {
        authenticatedClient = await loginToTradingView();
      }

      switch(type) {
        case 'get_indicators':
          try {
            const data = await getChartData(authenticatedClient, symbol, interval);
            ws.send(JSON.stringify(data));
          } catch (error) {
            logger.error(`Error getting indicators for ${symbol}:`, error);
            ws.send(JSON.stringify({
              type: 'error',
              symbol: symbol,
              message: error.toString()
            }));
          }
          break;
        
        case 'heartbeat':
          ws.send(JSON.stringify({ type: 'heartbeat', timestamp: new Date().toISOString() }));
          break;
        
        default:
          logger.warn(`Unknown request type: ${type}`);
          ws.send(JSON.stringify({ 
            type: 'error', 
            message: 'Unknown request type' 
          }));
      }
    } catch (error) {
      logger.error('Error processing message', { error });
      ws.send(JSON.stringify({ 
        type: 'error', 
        message: error.message 
      }));
    }
  });

  ws.on('close', () => {
    logger.info('Client disconnected from TradingView data service');
  });

  ws.on('error', (error) => {
    logger.error('WebSocket error', error);
  });
});

// Handle server-level errors
wss.on('error', (error) => {
  logger.error('WebSocket server error', error);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
});
