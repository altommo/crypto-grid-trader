class Backtester {
    constructor(formId, resultsContainer) {
        this.formElement = document.getElementById(formId);
        this.resultsContainer = document.getElementById(resultsContainer);
        this.init();
    }

    init() {
        this.formElement.addEventListener('submit', this.handleSubmit.bind(this));
    }

    async handleSubmit(event) {
        event.preventDefault();
        try {
            const days = document.getElementById('backtestDays').value;
            const response = await fetch('/api/backtest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ days: parseInt(days) })
            });
            
            const results = await response.json();
            if (results.error) {
                console.error('Backtest error:', results.error);
                return;
            }
            
            this.updateResults(results);
        } catch (error) {
            console.error('Error running backtest:', error);
        }
    }

    updateResults(results) {
        document.getElementById('totalReturn').textContent = 
            `${(results.total_return * 100).toFixed(2)}%`;
        document.getElementById('winRate').textContent = 
            `${(results.win_rate * 100).toFixed(2)}%`;
        document.getElementById('totalTrades').textContent = 
            results.total_trades;
    }
}

// Export for use in other modules
export default Backtester;