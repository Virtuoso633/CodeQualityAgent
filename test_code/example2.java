import java.util.*;

public class BadCodeExample {

    // Hardcoded password (Security issue)
    private static final String PASSWORD = "123456";

    // Global mutable variable (Bad practice)
    static List<Integer> globalList = new ArrayList<>();

    // Method with inefficient algorithm (Performance issue)
    public static double calculateAverage(List<Integer> numbers) {
        int total = 0;
        for (int i = 0; i < numbers.size(); i++) {
            total += numbers.get(i); // Repeated calls to get() (O(n) in some list types)
        }
        return total / numbers.size(); // Integer division (Bug: loses precision)
    }

    // Memory-heavy operation (Performance issue)
    public static void createHugeList() {
        List<Integer> huge = new ArrayList<>();
        for (int i = 0; i < 1_000_000; i++) {
            huge.add(i * i); // unnecessary big list stored in memory
        }
        globalList = huge; // Leaks memory globally
    }

    // Dangerous method: SQL Injection risk
    public static void insecureLogin(String username, String password) {
        String query = "SELECT * FROM users WHERE name='" + username + "' AND pass='" + password + "'";
        System.out.println("Executing query: " + query);
        // Pretend to execute query (insecure concatenation)
    }

    // Overly broad exception handling
    public static void riskyMethod() {
        try {
            int[] nums = new int[5];
            nums[10] = 100; // Index out of bounds
        } catch (Exception e) {
            // Swallowing exception, no logging
        }
    }

    // Dead code (unreachable)
    public static void deadCode() {
        if (false) {
            System.out.println("This will never run!");
        }
    }

    public static void main(String[] args) {
        // Precision issue: integer division
        List<Integer> nums = Arrays.asList(1, 2, 3, 4, 5);
        double avg = calculateAverage(nums);
        System.out.println("Average: " + avg);

        // Security issue
        System.out.println("Password in code: " + PASSWORD);

        // Performance issue
        createHugeList();

        // SQL injection issue
        insecureLogin("admin", "' OR '1'='1");

        // Exception swallowing
        riskyMethod();

        // Dead code test
        deadCode();
    }
}
