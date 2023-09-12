"""
This module includes some test to check
the McM REST module and the authentication mechanisms.
"""
from rest import McM
import unittest
import os
import logging


class BaseTest(unittest.TestCase):
    """
    This test case includes some features to build other TestCases
    like the logger and checking if some packages are available.
    """
    def build(self):
        """
        Sets some default attributes for the test
        """
        self.skip_sso_cookie_test = False

    def package_available(self, package):
        """
        Check, via shell execution, if a desired package is available into the runtime
        environment.

        Args:
            package (str): Package to verify if exists

        Returns:
            bool: True if the package exists, False otherwise
        """
        result = os.system("which %s" % package)
        return result == 0

    def skip_cookie_tests(self):
        """
        Check if the runtime environment has the packages required to request
        session cookies via Kerberos authentication. If the are not available,
        this will skip all the test related with cookies and browser emulation
        (by convention, this tests will include the string: sso_cookie into its name)
        """
        # Is auth-get-sso-cookie package available?
        cookie_package = "auth-get-sso-cookie"
        cookie_package_available = self.package_available(
            package=cookie_package
        )
        kerberos_available = self.package_available(
            package="kinit"
        ) and self.package_available(package="klist")
        if not cookie_package_available:
            logging.warn(
                "auth-get-sso-cookie package is not available, cookie test will be skipped"
            )
            self.skip_sso_cookie_test = True
        if not kerberos_available:
            logging.warn("Kerberos is not available, cookie test will be skipped")
            self.skip_sso_cookie_test = True

    def __remove_cookies(self):
        """
        This tries to remove the session cookies if they are
        available in the filesystem.
        """
        home = os.getenv("HOME")
        dev_cookie_path = "%s/private/mcm-dev-cookie.txt" % (home)
        prod_cookie_path = "%s/private/mcm-prod-cookie.txt" % (home)
        try:
            os.remove(dev_cookie_path)
            os.remove(prod_cookie_path)
        except OSError:
            # Supress the error if some file doesn't exist
            pass

    def setUp(self):
        """
        Prepare the test case
        """
        self.build()
        self.skip_cookie_tests()
        self.__remove_cookies()

    def test_module(self):
        """
        Check that we are able to use the McM module
        with the desired authentication method.
        """
        if isinstance(self, BaseTest) and type(self) == BaseTest:
            raise unittest.SkipTest("This execution is related to the BaseTest, skip it")

        test_prepid = "TOP-Summer12-00368"
        single_request = self.mcm.get("requests", test_prepid, method="get")
        self.assertIsNotNone(single_request, "The request exists in McM and its information should be available")
        self.assertIsInstance(single_request, dict, "This should have the request information as a dictionary")
        self.assertEqual(test_prepid, single_request["prepid"], "The retrieved request is not the desired one")


class SSOTestDevelopment(BaseTest):
    """
    This test checks that the McM REST module
    works properly with session cookies for the development
    environment. Please make sure to use Kerberos credentials
    for an account that does not have 2FA enabled.
    """
    def setUp(self):
        super(SSOTestDevelopment, self).setUp()
        self.mcm = McM(McM.SSO, dev=True)
    
    def test_module(self):
        if self.skip_sso_cookie_test:
            raise unittest.SkipTest("CERN Auth CLI packages are not available")
        return super(SSOTestDevelopment, self).test_module()
    

class SSOTestProduction(BaseTest):
    """
    This test checks that the McM REST module
    works properly with session cookies for the production
    environment. Please make sure to use Kerberos credentials
    for an account that does not have 2FA enabled.
    """
    def setUp(self):
        super(SSOTestProduction, self).setUp()
        self.mcm = McM(McM.SSO, dev=False)
    
    def test_module(self):
        if self.skip_sso_cookie_test:
            raise unittest.SkipTest("CERN Auth CLI packages are not available")
        return super(SSOTestProduction, self).test_module()
    

class IDToken(BaseTest):
    """
    This test checks that McM REST module works properly
    by requesting an ID token for authenticating user actions.
    To complete the test properly,
    it is required human intervention.
    """
    def setUp(self):
        super(IDToken, self).setUp()
        # Set the CLIENT_SECRET for development environment
        os.environ["MCM_CLIENT_SECRET"] = os.getenv("DEV_MCM_CLIENT_SECRET")
        self.mcm = McM(McM.OIDC, dev=True)


class IDTokenExpiredDevelopment(BaseTest):
    """
    This test checks that McM REST module is able to
    refresh ID tokens properly if they have already expired.
    To complete the test properly,
    it is required human intervention.
    """
    def setUp(self):
        super(IDTokenExpiredDevelopment, self).setUp()
        # Set the CLIENT_SECRET for development environment
        os.environ["MCM_CLIENT_SECRET"] = os.getenv("DEV_MCM_CLIENT_SECRET")
        self.mcm = McM(McM.OIDC, dev=True)
        # Set an invalid JWT token before doing the request.
        # Token retrieved from: https://jwt.io/
        # Default 'John Doe' token
        invalid_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
            "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        self.mcm.token = invalid_token
    

if __name__ == "__main__":
    unittest.main()