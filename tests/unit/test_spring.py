"""Test spring module."""
import unittest

from config.spring import ConfigServer


class TestUtils(unittest.TestCase):
    """Unit tests to spring module."""

    def setUp(self):
        """Mock of responses generated by Spring Cloud Config."""
        self.config_example = {
            "health": {
                "config": {
                    "enabled": False
                }
            },
            "spring": {
                "cloud": {
                    "consul": {
                        "discovery": {
                            "health-check-interval": "10s",
                            "health-check-path": "/manage/health",
                            "instance-id": "pecas-textos:${random.value}",
                            "prefer-ip-address": True,
                            "register-health-check": True
                        },
                        "host": "discovery",
                        "port": 8500
                    }
                }
            }
        }

    def test_connection_failed_to_configserver(self):
        """Test failed to connect on configserver."""
        with self.assertRaises(SystemExit):
            ConfigServer()


if __name__ == '__main__':
    unittest.main()
