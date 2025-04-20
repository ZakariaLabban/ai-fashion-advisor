import time
import asyncio
import aiohttp
import logging
from prometheus_client import start_http_server, Gauge, Counter, Info

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define Prometheus metrics
SERVICE_UP = Gauge('service_up', 'Service health status (1=up, 0=down)', ['service'])
API_LATENCY = Gauge('api_latency', 'API response time in seconds', ['service', 'endpoint'])
API_REQUESTS = Counter('api_requests', 'Count of API requests', ['service', 'endpoint', 'status'])
SERVICE_INFO = Info('service_info', 'Service information', ['service'])
EEP_ISSUE = Gauge('eep_health_check_wrong_path', 'Count of EEP health check requests with wrong path', ['service'])

# Define the services to monitor with more detailed configuration
SERVICES = {
    'eep': {
        'host': 'eep',
        'port': 9000,
        'endpoints': {
            '/health': {'method': 'GET'},
            '/api/analyze/health': {'method': 'GET'},
            '/services/health': {'method': 'GET'},
        },
        'description': 'External Endpoint Processor'
    },
    'detection-iep': {
        'host': 'detection-iep',
        'port': 8001,
        'endpoints': {
            '/health': {'method': 'GET'}
        },
        'expected_model': 'YOLOv8 Detection',
        'description': 'Clothing Detection Service'
    },
    'style-iep': {
        'host': 'style-iep',
        'port': 8002,
        'endpoints': {
            '/health': {'method': 'GET'}
        },
        'expected_model': 'YOLOv8 Style Classification',
        'description': 'Style Classification Service'
    },
    'feature-iep': {
        'host': 'feature-iep',
        'port': 8003,
        'endpoints': {
            '/health': {'method': 'GET'}
        },
        'description': 'Feature Extraction Service'
    },
    'virtual-tryon-iep': {
        'host': 'virtual-tryon-iep',
        'port': 8004,
        'endpoints': {
            '/health': {'method': 'GET'}
        },
        'expected_model': 'Virtual Try-On',
        'description': 'Virtual Try-On Service'
    },
    'elegance-iep': {
        'host': 'elegance-iep',
        'port': 8005,
        'endpoints': {
            '/health': {'method': 'GET'}
        },
        'description': 'Fashion Chatbot Service'
    },
    'reco-data-iep': {
        'host': 'reco-data-iep',
        'port': 8007,
        'endpoints': {
            '/health': {'method': 'GET'}
        },
        'description': 'Recommendation Data Service'
    },
    'match-iep': {
        'host': 'match-iep',
        'port': 8008,
        'endpoints': {
            '/health': {'method': 'GET'}
        },
        'description': 'Outfit Matching Service'
    },
    'text2image-iep': {
        'host': 'text2image-iep',
        'port': 8020,
        'endpoints': {
            '/health': {'method': 'GET'}
        },
        'description': 'Text to Image Search Service'
    },
    'ppl-detector-iep': {
        'host': 'ppl-detector-iep',
        'port': 8009,
        'endpoints': {
            '/health': {'method': 'GET'}
        },
        'expected_model': 'YOLOv8 Person Detection',
        'description': 'Person Detection Service'
    }
}

# Monitor EEP wrong health check requests
async def monitor_eep_health_check_issue():
    """
    Special monitoring for the EEP service issue where it's requesting /health/health 
    instead of /health. This is to track the issue without changing the EEP service.
    """
    while True:
        for service_name, service_config in SERVICES.items():
            if service_name != 'eep':  # Only check for services other than EEP
                try:
                    async with aiohttp.ClientSession() as session:
                        wrong_path = f"http://{service_config['host']}:{service_config['port']}/health"
                        async with session.get(wrong_path, timeout=1) as response:
                            # If we get a 404, it means EEP is likely trying to access this wrong endpoint
                            EEP_ISSUE.labels(service=service_name).set(1 if response.status == 404 else 0)
                except:
                    # No need to log exceptions here, just continue
                    pass
        await asyncio.sleep(60)  # Check less frequently than the main health checks

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
                            # Create a dictionary of service information
                            info_dict = {
                                "description": service_config.get('description', 'Unknown service'),
                                "model": data.get('model', service_config.get('expected_model', 'unknown')),
                                "version": data.get('version', 'unknown'),
                                "status": data.get('status', 'healthy')
                            }
                            
                            # Record service info
                            SERVICE_INFO.labels(service=service_name).info(info_dict)
                            
                            logger.info(f"Service {service_name} info recorded")
                    except Exception as e:
                        # It's okay if we can't parse JSON
                        logger.debug(f"Could not parse JSON from {service_name}: {str(e)}")
                
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
    
    # Record basic info even if health check fails
    if not service_up:
        try:
            SERVICE_INFO.labels(service=service_name).info({
                "description": service_config.get('description', 'Unknown service'),
                "status": "unhealthy"
            })
        except Exception:
            pass
    
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

async def run_monitoring():
    """Run all monitoring tasks concurrently"""
    # Start the EEP issue monitoring in a separate task
    eep_monitor_task = asyncio.create_task(monitor_eep_health_check_issue())
    
    # Run the main service monitoring
    await monitor_services()
    
    # Cancel the EEP monitor task if the main task exits
    eep_monitor_task.cancel()

if __name__ == "__main__":
    # Start up the server to expose the metrics.
    start_http_server(8000)
    logger.info("Service monitor started on port 8000")
    
    # Start the monitoring loop
    asyncio.run(run_monitoring()) 