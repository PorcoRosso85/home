class DataProcessor:
    def calculate_average(self, numbers: list[float]) -> float:
        """Calculate the average of a list of numbers"""
        if not numbers:
            return 0.0
        return sum(numbers) / len(numbers)
    
    def process_data(self, data: list[float]) -> dict:
        """Process data and return statistics"""
        avg = self.calculate_average(data)  # Line 10: using the function
        return {
            "average": avg,
            "count": len(data)
        }


def main():
    processor = DataProcessor()
    
    # Multiple usages of calculate_average
    result1 = processor.calculate_average([1, 2, 3, 4, 5])  # Line 20
    print(f"Average 1: {result1}")
    
    result2 = processor.calculate_average([10, 20, 30])  # Line 23
    print(f"Average 2: {result2}")
    
    # Using through process_data
    stats = processor.process_data([5, 10, 15, 20])
    print(f"Stats: {stats}")


if __name__ == "__main__":
    main()