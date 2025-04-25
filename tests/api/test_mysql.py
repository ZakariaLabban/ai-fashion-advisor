import pytest
import os
import sys
from pathlib import Path
import mysql.connector
from mysql.connector import Error

# Add the parent directory to the Python path to import the Azure Key Vault helper
sys.path.append(str(Path(__file__).parent.parent.parent))

# Mark all tests in this file with the api marker
pytestmark = pytest.mark.api

# Try to import the Azure Key Vault helper, but don't fail if it's not available
try:
    from azure_keyvault_helper import AzureKeyVaultHelper
    # Initialize Azure Key Vault helper
    keyvault = AzureKeyVaultHelper()
    # Get credentials from Azure Key Vault with environment variable fallback
    MYSQL_HOST = keyvault.get_secret("MYSQL-HOST", os.getenv("MYSQL_HOST", "localhost"))
    MYSQL_PORT = int(keyvault.get_secret("MYSQL-PORT", os.getenv("MYSQL_PORT", "3306")))
    MYSQL_USER = keyvault.get_secret("MYSQL-USER", os.getenv("MYSQL_USER", "root"))
    MYSQL_PASSWORD = keyvault.get_secret("MYSQL-PASSWORD", os.getenv("MYSQL_PASSWORD", ""))
    MYSQL_DATABASE = keyvault.get_secret("MYSQL-DATABASE", os.getenv("MYSQL_DATABASE", "fashion_advisor"))
except (ImportError, ValueError) as e:
    print(f"Azure Key Vault not available: {e}. Using environment variables.")
    # Fall back to environment variables
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "fashion_advisor")

@pytest.fixture
def mysql_connection():
    """Create a MySQL connection for testing."""
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        
        yield connection
        
        # Close the connection after the test
        if connection.is_connected():
            connection.close()
            
    except Error as e:
        pytest.skip(f"Could not connect to MySQL: {e}")

@pytest.mark.live
def test_mysql_connection(mysql_connection):
    """Test the connection to MySQL."""
    assert mysql_connection.is_connected()
    print(f"Connected to MySQL database: {MYSQL_DATABASE} on {MYSQL_HOST}")

@pytest.mark.live
def test_mysql_basic_query(mysql_connection):
    """Test a basic query to MySQL."""
    try:
        # Create a cursor
        cursor = mysql_connection.cursor(dictionary=True)
        
        # Create a test table if it doesn't exist already
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_fashion_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(50) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Insert a test record
        cursor.execute("""
        INSERT INTO test_fashion_items (name, category, price)
        VALUES ('Test T-shirt', 'topwear', 29.99)
        """)
        mysql_connection.commit()
        
        # Query the inserted record
        cursor.execute("SELECT * FROM test_fashion_items WHERE name = 'Test T-shirt'")
        result = cursor.fetchone()
        
        # Clean up
        cursor.execute("DELETE FROM test_fashion_items WHERE name = 'Test T-shirt'")
        mysql_connection.commit()
        cursor.close()
        
        # Assertions
        assert result is not None
        assert result['name'] == 'Test T-shirt'
        assert result['category'] == 'topwear'
        assert float(result['price']) == 29.99
        
    except Error as e:
        pytest.fail(f"MySQL query failed: {e}") 