import unittest
import docker
import time
import requests

class TestDockerHttpdApache(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Setup Docker container with Apache HTTPD installation."""
        cls.client = docker.from_env()

        # Check if the container already exists, otherwise create it
        try:
            cls.container = cls.client.containers.get("httpd-container")
            print(f"Found existing container: {cls.container.name}")
        except docker.errors.NotFound:
            print("Container not found. Creating a new one...")
            cls.container = cls.client.containers.run(
                "httpd",  # Use the official httpd image
                name="httpd-container",
                detach=True,
                tty=True,
                stdin_open=True,
                ports={'80/tcp': 8080},  # Map port 80 in container to 8080 on host
            )
            print(f"Created new container: {cls.container.name}")

        # Wait for the container to be in running state
        cls.wait_for_container_to_be_running()

    @classmethod
    def tearDownClass(cls):
        """Cleanup after tests."""
        print("Tests complete. No need to remove container as it's already existing.")

    @classmethod
    def wait_for_container_to_be_running(cls, timeout=30):
        """Wait for the container to be in 'running' state."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            cls.container.reload()  # Reload the container to get its latest state
            if cls.container.status == 'running':
                print(f"Container {cls.container.name} is now running.")
                return
            print(f"Container {cls.container.name} is not running yet.")
            time.sleep(2)
        raise Exception(f"Container {cls.container.name} did not start within {timeout} seconds.")

    def test_container_running(self):
        """Test if the container 'httpd-container' is running."""
        self.container.reload()  # Reload the container's status
        self.assertEqual(self.container.status, "running", "Container 'httpd-container' is not running.")

    def test_apache_installed(self):
        """Test if Apache HTTP server is installed in the container."""
        # Use `httpd -v` instead of `apache2 -v` for the httpd image
        result = self.container.exec_run("httpd -v")
        self.assertIn("Apache", result.output.decode(), "Apache HTTP server is not installed.")

    def test_apache_service_running(self):
        """Test if Apache HTTP server is running."""
        # Since `ps` might not be available, we check if the httpd process is running
        result = self.container.exec_run("pgrep -fl httpd")
        self.assertGreater(len(result.output.decode()), 0, "Apache HTTP service is not running.")

    def test_apache_access(self):
        """Test if the Apache server is accessible via HTTP request."""
        try:
            # Access Apache via localhost:8080
            response = requests.get("http://localhost:8080")
            self.assertEqual(response.status_code, 200, "Failed to access Apache HTTP server.")
        except requests.exceptions.RequestException as e:
            self.fail(f"HTTP request failed: {e}")

if __name__ == "__main__":
    unittest.main()
