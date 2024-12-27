import unittest
import docker
import time
import requests
import subprocess
import json
import os


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
        result = self.container.exec_run("httpd -v")
        self.assertIn("Apache", result.output.decode(), "Apache HTTP server is not installed.")

    def test_apache_service_running(self):
        """Test if Apache HTTP server is running."""
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


class TestResultWithPercentage(unittest.TextTestRunner):
    def run(self, test):
        """Run the test suite and calculate passed percentage."""
        result = super().run(test)
        total_tests = result.testsRun
        passed_tests = total_tests - (len(result.failures) + len(result.errors))
        passed_percentage = (passed_tests / total_tests) * 100
        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed Tests: {passed_tests}")
        print(f"Passed Percentage: {passed_percentage:.2f}%")

        # Write the percentage to a file
        with open("test_results.txt", "w") as f:
            f.write(f"Passed Percentage: {passed_percentage:.2f}%\n")

        return result


class Git:
    @staticmethod
    def create_repository(repo_name, token):
        """Create a new repository on GitHub."""
        url = "https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {token}",
            "Content-Type": "application/json"
        }
        data = {"name": repo_name, "private": False}

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            print(f"Repository '{repo_name}' created successfully.")
        else:
            print(f"Failed to create repository: {response.json()}")

    @staticmethod
    def git_push(repo_name):
        """Push changes to GitHub."""
        try:
            # Initialize Git and push to the new repository
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "remote", "add", "origin", f"https://github.com/iihtmahesh/{repo_name}.git"],
                           check=True)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Add updated test results"], check=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
            print("Changes pushed to GitHub successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error pushing to GitHub: {e}")


if __name__ == "__main__":
    # GitHub Personal Access Token
    GITHUB_TOKEN = "your_github_personal_access_token"  # Replace with your token
    REPO_NAME = "output"

    # Create a new repository
    Git.create_repository(REPO_NAME, GITHUB_TOKEN)

    # Run the tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDockerHttpdApache)
    runner = TestResultWithPercentage(verbosity=2)
    result = runner.run(suite)

    # Push changes to GitHub if all tests pass
    if not result.failures and not result.errors:
        Git.git_push(REPO_NAME)
