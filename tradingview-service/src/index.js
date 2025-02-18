require('dotenv').config();
const WebSocket = require('ws');
const { createLogger, format, transports } = require('winston');
const TradingViewClient = require('./tradingview-client');

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

// Credentials from environment variables
const USERNAME = process.env.TRADINGVIEW_USERNAME;
const PASSWORD = process.env.TRADINGVIEW_PASSWORD;

// TradingView WebSocket Server Configuration
const PORT = process.env.PORT || 8765;
const wss = new WebSocket.Server({ port: PORT });

// Global authenticated client
let tradingViewClient = null;

// Initialize TradingView Client
async function initializeTradingViewClient() {
    try {
        logger.info('Initializing TradingView Client...');
        
        // Validate credentials
        if (!USERNAME || !PASSWORD) {
            throw new Error('TradingView username or password not provided');
        }

        // Create and login client
        tradingViewClient = new TradingViewClient(USERNAME, PASSWORD);
        await tradingViewClient.login();
        
        logger.info('TradingView Client initialized successfully');
    } catch (error) {
        logger.error('Failed to initialize TradingView Client:', error);
        throw error;
    }
}

// Initial client initialization
initializeTradingViewClient().catch(err => {
    logger.error('Initial TradingView Client setup failed:', err);
});

logger.info(`TradingView WebSocket server running on port ${PORT}`);

wss.on('connection', (ws) => {
  logger.info('New client connected to TradingView data service');

  ws.on('message', async (rawMessage) => {
    try {
      const message = JSON.parse(rawMessage);
      const { type, symbol, interval } = message;

      logger.info(`Received request: ${JSON.stringify(message)}`);

      // Ensure client is initialized
      if (!tradingViewClient) {
        await initializeTradingViewClient();
      }

      switch(type) {
        case 'get_indicators':
          try {
            const chartData = await tradingViewClient.getChartData(symbol, interval);
            ws.send(JSON.stringify({
              type: 'market_update',
              ...chartData
            }));
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
          ws.send(JSON.stringify({ 
            type: 'heartbeat', 
            timestamp: new Date().toISOString() 
          }));
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
