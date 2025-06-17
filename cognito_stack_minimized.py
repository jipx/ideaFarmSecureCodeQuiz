from aws_cdk import (
    Stack,
    aws_cognito as cognito,
    CfnOutput
)
from constructs import Construct

class GamifiedCognitoStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Read callback URL from context
        callback_url = self.node.try_get_context("cognitoCallbackUrl") or "https://example.com"

        # Cognito User Pool
        user_pool = cognito.UserPool(
            self, "GamifiedUserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(username=True, email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_digits=True,
                require_lowercase=True,
                require_uppercase=True,
                require_symbols=False
            )
        )

        # Cognito App Client
        user_pool_client = cognito.UserPoolClient(
            self, "GamifiedUserPoolClient",
            user_pool=user_pool,
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                callback_urls=[callback_url, "http://localhost:3000/"],
                logout_urls=[callback_url, "http://localhost:3000/"]
            )
        )

        # Outputs
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id, export_name="UserPoolId")
        CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id, export_name="UserPoolClientId")