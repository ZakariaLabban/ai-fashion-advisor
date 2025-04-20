import time
import asyncio
import aiohttp
import logging
from prometheus_client import start_http_server, Gauge, Counter

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define Prometheus metrics
SERVICE_UP = Gauge('service_up', 'Service health status (1=up, 0=down)', ['service'])
API_LATENCY = Gauge('api_latency', 'API response time in seconds', ['service', 'endpoint'])
API_REQUESTS = Counter('api_requests', 'Count of API requests', ['service', 'endpoint', 'status'])
SERVICE_INFO = Gauge('service_info', 'Service information', ['service', 'version', 'model'])

# Define the services to monitor with more detailed configuration
SERVICES = {
    'eep': {
        'host': 'eep',
        'port': 9000,
        'endpoints': {
            '/health': {'method': 'GET'},
            '/api/analyze/health': {'method': 'GET'},
            '/services/health': {'method': 'GET'},
        }
    },
    'detection-iep': {
        'host': 'detection-iep',
        'port': 8001,
        'endpoints': {
            '/health': {'method': 'GET'}
        },
        'expected_model': 'YOLOv8 Detection'
    },
    'style-iep': {
        'host': 'style-iep',
        'port': 8002,
        'endpoints': {
            '/health': {'method': 'GET'}
        },
        'expected_model': 'YOLOv8 Style Classification'
    },
    'feature-iep': {
        'host': 'feature-iep',
        'port': 8003,
        'endpoints': {
            '/health': {'method': 'GET'}
        }
    },
    'virtual-tryon-iep': {
        'host': 'virtual-tryon-iep',
        'port': 8004,
        'endpoints': {
            '/health': {'method': 'GET'}
        },
        'expected_model': 'Virtual Try-On'
    },
    'elegance-iep': {
        'host': 'elegance-iep',
        'port': 8005,
        'endpoints': {
            '/health': {'method': 'GET'}
        }
    },
    'reco-data-iep': {
        'host': 'reco-data-iep',
        'port': 8007,
        'endpoints': {
            '/health': {'method': 'GET'}
        }
    },
    'match-iep': {
        'host': 'match-iep',
        'port': 8008,
        'endpoints': {
            '/health': {'method': 'GET'}
        }
    },
    'text2image-iep': {
        'host': 'text2image-iep',
        'port': 8020,
        'endpoints': {
            '/health': {'method': 'GET'}
        }
    },
    'ppl-detector-iep': {
        'host': 'ppl-detector-iep',
        'port': 8009,
        'endpoints': {
            '/health': {'method': 'GET'}
        },
        'expected_model': 'YOLOv8 Person Detection'
    }
}

async def check_endpoint(session, service_name, service_config, endpoint, config):
    """Check a specific endpoint and record metrics"""
    url = f"http://{service_config['host']}:{service_config['port']}{endpoint}"
    method = config.get('method', 'GET')
    
    try:
        start_time = time.time()
        if method == 'GET':
            async with session.get(url, timeout=5) as response:
                duration = time.time() - start_time
                status = response.status
                API_LATENCY.labels(service=service_name, endpoint=endpoint).set(duration)
                API_REQUESTS.labels(service=service_name, endpoint=endpoint, status=status).inc()
                
                # Try to parse JSON for additional info if status is good
                if status < 400:
                    try:
                        data = await response.json()
                        if isinstance(data, dict):
                            # Extract version and model info if available
                            version = data.get('version', 'unknown')
                            model = data.get('model', service_config.get('expected_model', 'unknown'))
                            
                            # Record service info
                            SERVICE_INFO.labels(
                                service=service_name, 
                                version=version,
                                model=model
                            ).set(1)
                            
                            logger.info(f"Service {service_name} info - version: {version}, model: {model}")
                    except Exception as e:
                        # It's okay if we can't parse JSON
                        pass
                
                logger.info(f"Checked {service_name} {endpoint}: status={status}, latency={duration:.3f}s")
                return status < 400
        # Add support for other methods if needed
        return False
    except Exception as e:
        logger.error(f"Error checking {url}: {str(e)}")
        API_REQUESTS.labels(service=service_name, endpoint=endpoint, status="error").inc()
        return False

async def check_service(session, service_name, service_config):
    """Check all endpoints of a service and update its status"""
    results = []
    for endpoint, config in service_config['endpoints'].items():
        result = await check_endpoint(session, service_name, service_config, endpoint, config)
        results.append(result)
    
    # Service is up if at least one endpoint is successfully checked
    service_up = any(results)
    SERVICE_UP.labels(service=service_name).set(1 if service_up else 0)
    logger.info(f"Service {service_name} overall status: {'UP' if service_up else 'DOWN'}")

async def monitor_services():
    """Main monitoring loop"""
    # Create a persistent aiohttp session
    timeout = aiohttp.ClientTimeout(total=10)
    connector = aiohttp.TCPConnector(limit=100, force_close=True, enable_cleanup_closed=True)
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        while True:
            tasks = []
            for service_name, service_config in SERVICES.items():
                task = check_service(session, service_name, service_config)
                tasks.append(task)
            
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.info("Completed service check cycle")
            except Exception as e:
                logger.error(f"Error during service check cycle: {str(e)}")
            
            # Wait before next check cycle
            await asyncio.sleep(15)  # Check every 15 seconds

if __name__ == "__main__":
    # Start up the server to expose the metrics.
    start_http_server(8000)
    logger.info("Service monitor started on port 8000")
    
    # Start the monitoring loop
    asyncio.run(monitor_services()) 