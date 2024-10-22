# db_connection.py

import mysql.connector
from mysql.connector import pooling

# Database configuration
db_config = {
    'user': 'SANKA',
    'password': '3Sssmalaka@!',
    'host': '192.168.10.52',  # e.g., 'localhost' or an IP address
    'database': 'GLEAMM_NIRE',
    'raise_on_warnings': True
}

# Create a connection pool
connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="my_pool",
    pool_size=5,
    pool_reset_session=True,  # Resets session variables when connection is returned to the pool
    **db_config
)

def get_connection():
    """
    Retrieves a connection from the pool.
    """
    connection1 = mysql.connector.connect(
        host='192.168.10.52',
        user='SANKA',
        password='3Sssmalaka@!',
        database='GLEAMM_NIRE'
    )
    
    connection2 = mysql.connector.connect(
        host='192.168.10.52',
        user='SANKA',
        password='3Sssmalaka@!',
        database='GLEAMM_NIRE_meters'
    )
    return connection1, connection2
