from app import create_app
from app.extensions import socketio
import logging
import socket
import os
import sys
import signal
import subprocess

# Configure basic logging for the server process
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Suppress verbose socketio logs for better performance
logging.getLogger('socketio').setLevel(logging.WARNING)
logging.getLogger('engineio').setLevel(logging.WARNING)

app = create_app()

def find_available_port(start_port=5000, end_port=6000):
    """
    Finds an available port in the specified range by attempting to bind a socket.
    Uses SO_REUSEADDR to ensure port is immediately available after restart.
    
    Args:
        start_port (int): The first port to try.
        end_port (int): The last port to try (inclusive).
        
    Returns:
        int: An available port number.
        
    Raises:
        RuntimeError: If no available port is found in the specified range.
    """
    for port in range(start_port, end_port + 1):
        try:
            # Create socket with SO_REUSEADDR to avoid "Address already in use" errors
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # On Windows, also set SO_EXCLUSIVEADDRUSE to be explicit
                if sys.platform == 'win32':
                    try:
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                    except (AttributeError, OSError):
                        pass
                s.bind(('0.0.0.0', port))
                logger.info(f"✓ Found available port: {port}")
                return port
        except OSError as e:
            logger.debug(f"Port {port} is in use or unavailable: {e}")
            continue
    raise RuntimeError(f"No available port found in range {start_port}-{end_port}")


def kill_existing_process_on_port(port):
    """
    Kills any existing process using the specified port (Windows-specific).
    """
    if sys.platform != 'win32':
        return
    
    try:
        # Find process using the port on Windows
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) > 0:
                    pid = parts[-1]
                    try:
                        subprocess.run(['taskkill', '/PID', pid, '/F'], timeout=5)
                        logger.info(f"Killed process {pid} holding port {port}")
                        return
                    except Exception as e:
                        logger.debug(f"Could not kill process {pid}: {e}")
    except Exception as e:
        logger.debug(f"Could not find/kill process on port {port}: {e}")


def graceful_shutdown(signum, frame):
    """Handle graceful shutdown on Ctrl+C."""
    logger.info("\n✓ Shutting down server gracefully (Ctrl+C received)...")
    sys.exit(0)


if __name__ == '__main__':
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, graceful_shutdown)
    
    try:
        # Get starting port from environment variable (FLASK_RUN_PORT) or use default 5000
        initial_port = int(os.environ.get('FLASK_RUN_PORT', 5000))
        
        # Try to find an available port, with fallback to killing existing process
        try:
            chosen_port = find_available_port(start_port=initial_port, end_port=initial_port + 100)
        except RuntimeError:
            logger.warning(f"Could not find free port in range. Attempting to free port {initial_port}...")
            kill_existing_process_on_port(initial_port)
            chosen_port = find_available_port(start_port=initial_port, end_port=initial_port + 100)
        
        logger.info(f"{'='*60}")
        logger.info(f"Starting Flask-SocketIO server on http://0.0.0.0:{chosen_port}")
        logger.info(f"{'='*60}")
        
        # Run SocketIO with optimizations
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=chosen_port, 
            debug=False, 
            use_reloader=False
        )
    except RuntimeError as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server shutdown initiated by user (Ctrl+C).")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Flask-SocketIO server terminated unexpectedly: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Flask-SocketIO server process has exited.")