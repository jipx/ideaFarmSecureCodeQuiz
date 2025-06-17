from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_sqs as sqs,
    aws_iam as iam,
    Duration
)
from aws_cdk.aws_lambda_event_sources import SqsEventSource
from constructs import Construct

class GamifiedBackendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB table
        session_table = dynamodb.Table(
            self, "SessionTable",
            partition_key={"name": "sessionId", "type": dynamodb.AttributeType.STRING},
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        # DLQ for quizgen
        quizgen_dlq = sqs.Queue(self, "QuizGenDLQ")

        # SQS Queues
        quizgen_queue = sqs.Queue(
            self, "QuizGenQueue",
        #make sure visibility_timeout is bigger than lambda timeout()
            visibility_timeout=Duration.seconds(60),
            dead_letter_queue=sqs.DeadLetterQueue(
        #retries failed message 3 times,then moves to the Dead Letter Queue
                max_receive_count=3,
                queue=quizgen_dlq
            )
        )
        evaluation_queue = sqs.Queue(self, "EvaluationQueue")
        record_queue = sqs.Queue(self, "RecordQueue")

        # Submit Lambda
        submit_fn = lambda_.Function(
            self, "SubmitFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="submit.lambda_handler",
            code=lambda_.Code.from_asset("lambda"),
            environment={
                "SESSION_TABLE": session_table.table_name,
                "QUIZGEN_QUEUE_URL": quizgen_queue.queue_url,
                "EVALUATION_QUEUE_URL": evaluation_queue.queue_url,
                "RECORD_QUEUE_URL": record_queue.queue_url
            }
        )
        session_table.grant_read_write_data(submit_fn)
        quizgen_queue.grant_send_messages(submit_fn)
        evaluation_queue.grant_send_messages(submit_fn)
        record_queue.grant_send_messages(submit_fn)

        # Get Result Lambda
        result_fn = lambda_.Function(
            self, "GetResultFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="get_result.lambda_handler",
            code=lambda_.Code.from_asset("lambda"),
            environment={
                "SESSION_TABLE": session_table.table_name
            }
        )
        session_table.grant_read_data(result_fn)

        # QuizGen Lambda
        quizgen_fn = lambda_.Function(
            self, "QuizGenFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="quizgen.lambda_handler",
            code=lambda_.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),#Set timeout to 30 seconds
            #only one quiz is processed at a time (to avooid Bedrock API throttling)
            #reserved_concurrent_executions=1,
            environment={
                "SESSION_TABLE": session_table.table_name,
                "AGENT_ID": "your-agent-id",
                "AGENT_ALIAS_ID": "your-alias-id",
                "BEDROCK_REGION": "ap-northeast-1"
            }
        )
        session_table.grant_read_write_data(quizgen_fn)
        quizgen_queue.grant_consume_messages(quizgen_fn)

        #batch_size=1, ensure single-message processing for clean observability and debugging
        quizgen_fn.add_event_source(SqsEventSource(quizgen_queue, batch_size=1))

        quizgen_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeAgent"],
                resources=["*"]
            )
        )

        # API Gateway
        api = apigateway.RestApi(self, "QuizApi")

        generate = api.root.add_resource("generate-quiz")
        generate.add_method("POST", apigateway.LambdaIntegration(submit_fn))

        result = api.root.add_resource("quiz-result")
        result.add_method("GET", apigateway.LambdaIntegration(result_fn))