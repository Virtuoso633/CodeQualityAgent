# Simple Python code for testing
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total / len(numbers)

# Some potential issues for testing
password = "123456"  # Security issue
x = [i*i for i in range(1000000)]  # Performance issue

if __name__ == "__main__":
    nums = [1, 2, 3, 4, 5]
    avg = calculate_average(nums)
    print(f"Average: {avg}")
