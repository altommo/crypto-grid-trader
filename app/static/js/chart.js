console.log('Chart.js loading...');

class TradingChart {
    constructor(containerId) {
        console.log('TradingChart constructor called for:', containerId);
        this.containerId = containerId;
        this.chart = null;
        this.candleSeries = null;
        this.currentSymbol = 'BTC/USDT';
        this.currentTimeframe = '1h';
        this.init();
    }

    init() {
        console.log('Initializing chart...');
        try {
            const container = document.getElementById(this.containerId);
            if (!container) {
                throw new Error(`Container ${this.containerId} not found`);
            }
            console.log('Container found:', container);

            // Create chart
            this.chart = window.LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: container.clientHeight,
                layout: {
                    background: { color: '#ffffff' },
                    textColor: '#333333',
                },
                grid: {
                    vertLines: { color: '#f0f0f0' },
                    horzLines: { color: '#f0f0f0' },
                },
                timeScale: {
                    timeVisible: true,
                    secondsVisible: false,
                },
            });
            console.log('Chart created:', this.chart);

            // Create candlestick series
            this.candleSeries = this.chart.addCandlestickSeries();
            console.log('Candlestick series created:', this.candleSeries);

            // Add sample data
            const sampleData = [
                { time: '2024-02-01', open: 100, high: 105, low: 96, close: 102 },
                { time: '2024-02-02', open: 102, high: 108, low: 100, close: 105 },
                { time: '2024-02-03', open: 105, high: 106, low: 98, close: 100 },
                { time: '2024-02-04', open: 100, high: 110, low: 98, close: 108 },
                { time: '2024-02-05', open: 108, high: 112, low: 105, close: 110 }
            ];
            console.log('Setting sample data:', sampleData);
            this.candleSeries.setData(sampleData);

            // Handle window resize
            window.addEventListener('resize', () => {
                this.chart.applyOptions({
                    width: container.clientWidth,
                    height: container.clientHeight
                });
            });

            console.log('Chart initialization complete');
            return true;
        } catch (error) {
            console.error('Error in chart initialization:', error);
            throw error;
        }
    }

    async loadData() {
        try {
            const response = await fetch(`/api/historical_data?symbol=${this.currentSymbol}&timeframe=${this.currentTimeframe}`);
            const data = await response.json();
            
            if (Array.isArray(data)) {
                console.log('Received data:', data.slice(0, 2), '... (first 2 of', data.length, 'entries)');
                this.candleSeries.setData(data);
            } else {
                console.error('Invalid data format received:', data);
            }
        } catch (error) {
            console.error('Error loading data:', error);
        }
    }
}

console.log('Chart.js loaded successfully');
export default TradingChart;