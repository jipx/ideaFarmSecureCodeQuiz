#!/usr/bin/env python3
import os
import aws_cdk as cdk

from cognito_stack_minimized import GamifiedCognitoStack
from backend_stack_combined import GamifiedBackendStack

app = cdk.App()

# Deploy Cognito/Auth Stack
auth_stack = GamifiedCognitoStack(app, "GamifiedCognitoStack")

# Deploy Backend Stack (imports values from Cognito)
backend_stack = GamifiedBackendStack(app, "GamifiedBackendStack")

app.synth()