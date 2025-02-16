class GridStrategy:
    def __init__(self, config):
        self.config = config
        self.grid_levels = []

    def initialize_grid(self, current_price):
        """
        Initialize grid levels around the current price
        """
        grid_size = self.config['trading']['grid_size']
        grid_spacing = self.config['trading']['grid_spacing']
        position_size = self.config['trading']['position_size']

        # Calculate grid levels
        self.grid_levels = []
        for i in range(-grid_size // 2, grid_size // 2 + 1):
            level_price = current_price * (1 + i * grid_spacing)
            self.grid_levels.append(GridLevel(level_price, position_size))

        return self.grid_levels

class GridLevel:
    def __init__(self, price, position_size):
        self.price = price
        self.position_size = position_size