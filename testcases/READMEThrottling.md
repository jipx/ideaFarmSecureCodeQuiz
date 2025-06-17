# Gamified OWASP Quiz System – Serverless & Throttled Design

This project provides a secure, serverless platform for generating and evaluating gamified OWASP Top 10 quizzes using Amazon Bedrock Agents, Lambda, SQS, and DynamoDB.


---

## 🖼️ Architecture Diagram

![Architecture Diagram](aws_architecture_diagram.png)

This diagram shows the interaction between:
- Client (React/Streamlit) authenticated via Amazon Cognito
- API Gateway forwarding requests to Lambda
- SQS decoupling the frontend from quiz generation
- Lambda fetching results from Bedrock Agents and updating DynamoDB


---

## 🧠 Key Components

- **Frontend**: React (or Streamlit) + Cognito Login
- **API Gateway**: Connects client to backend
- **Lambda Functions**: Handles quiz generation, result retrieval, status updates
- **Amazon SQS**: Decouples front-end requests from Bedrock agent calls
- **DynamoDB**: Stores session state, quiz, and metadata
- **Amazon Bedrock Agent**: Generates secure coding quizzes (Claude or Titan)
- **CDK**: Full infrastructure-as-code deployment

---

## 🧭 Lambda Throttling Configuration (SQS Trigger)

To prevent overloading the Bedrock agent or downstream systems, the Lambda triggered by SQS is throttled using:

| Setting                     | Value     |
|-----------------------------|-----------|
| SQS Batch Size              | `1`       |
| Lambda Reserved Concurrency | `1`       |
| Lambda Timeout              | `30s`     |
| SQS Visibility Timeout      | `60s`     |
| DLQ                         | Enabled (3 retries) |

### CDK Snippet

```python
quizgen_fn = lambda_.Function(
    self, "QuizgenFunction",
    runtime=lambda_.Runtime.PYTHON_3_11,
    handler="quizgen.lambda_handler",
    code=lambda_.Code.from_asset("lambda"),
    reserved_concurrent_executions=1,
    timeout=Duration.seconds(30),
    environment={...}
)

quiz_queue = sqs.Queue(
    self, "QuizGenQueue",
    visibility_timeout=Duration.seconds(60),
    dead_letter_queue=sqs.DeadLetterQueue(
        max_receive_count=3,
        queue=sqs.Queue(self, "QuizGenDLQ")
    )
)

quizgen_fn.add_event_source(
    lambda_event_sources.SqsEventSource(
        quiz_queue,
        batch_size=1
    )
)
```

Use this setup to safely rate-limit quiz generation requests via SQS → Lambda.

---
---

## 📈 Monitoring & Tuning

### CloudWatch Metrics

| Resource | Metric                      | Use to detect                     |
|----------|-----------------------------|-----------------------------------|
| Lambda   | `Invocations`, `Errors`     | Function activity and failures    |
| Lambda   | `Throttles`                 | If concurrency needs tuning       |
| Lambda   | `IteratorAge`               | Message processing delays         |
| SQS      | `ApproximateNumberOfMessagesVisible` | Queue backlog               |
| SQS      | `NumberOfMessagesSentToDLQ` | Failed messages after retries     |

### Best Practices

- Set **Lambda timeout < Visibility timeout**
- Enable **Dead Letter Queue (DLQ)**
- Use **batch size = 1** for serial execution
- Monitor **DLQ content** to debug failures
- Use **reserved concurrency = 1** to throttle

---

## 🧪 Traffic Simulation Script

A Python script is available to simulate traffic by pushing both valid and malformed quiz generation requests to the SQS queue.

### Script: `send_test_messages.py`

```python
import boto3, json, time, uuid

QUEUE_URL = "https://sqs.<region>.amazonaws.com/<account-id>/<queue-name>"
sqs = boto3.client("sqs")

# Send valid messages
for i in range(10):
    msg = {
        "sessionId": f"valid-{uuid.uuid4()}",
        "category": "SQL Injection",
        "difficulty": "medium"
    }
    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(msg))
    time.sleep(1)

# Send malformed messages
bad = { "difficulty": "easy" }  # Missing required fields
sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(bad))
```

Use this to observe:
- Retry behavior
- DLQ routing
- Visibility timeout impact
- Lambda error logging in CloudWatch

---

## 📊 CloudWatch Monitoring Dashboard (Optional)

You can create a custom CloudWatch dashboard to monitor Lambda and SQS performance in real time.

### Recommended Widgets

| Widget Type   | Metric Source | Metric Name                        |
|---------------|---------------|------------------------------------|
| Line          | Lambda        | Invocations, Errors, Throttles     |
| Line          | Lambda        | Duration, IteratorAge              |
| Line          | SQS           | ApproximateNumberOfMessagesVisible |
| Line          | SQS           | NumberOfMessagesSentToDLQ          |
| Single Value  | Lambda        | ConcurrentExecutions               |

### Example CDK Snippet (Dashboard)

```python
from aws_cdk import aws_cloudwatch as cw

dashboard = cw.Dashboard(self, "QuizMonitoringDashboard")

dashboard.add_widgets(
    cw.GraphWidget(
        title="Lambda Invocations",
        left=[cw.Metric(namespace="AWS/Lambda", metric_name="Invocations", dimensions_map={"FunctionName": quizgen_fn.function_name})]
    ),
    cw.GraphWidget(
        title="SQS Queue Depth",
        left=[cw.Metric(namespace="AWS/SQS", metric_name="ApproximateNumberOfMessagesVisible", dimensions_map={"QueueName": quiz_queue.queue_name})]
    )
)
```

📌 You can also create this manually in the AWS Console under **CloudWatch > Dashboards**.

---

## 🔧 Tuning Based on CloudWatch Metrics

Monitor your Lambda-SQS system and tune based on the following signals:

### 1. `IteratorAge` (Lambda)
- 📈 **What it means**: Delay between message arrival and processing
- 🛠️ **Action**: Increase `reserved_concurrent_executions` or reduce processing time

### 2. `Throttles` (Lambda)
- 📈 **What it means**: Lambda is receiving more concurrent invocations than allowed
- 🛠️ **Action**: Increase `reserved_concurrent_executions` or stagger traffic (e.g., reduce SQS batch)

### 3. `Errors` or `DLQ` increase
- 📈 **What it means**: Your Lambda is failing or cannot handle certain messages
- 🛠️ **Action**: 
  - Check Lambda logs for stack traces
  - Validate malformed messages
  - Add more robust validation or fallbacks

### 4. `ApproximateNumberOfMessagesVisible` (SQS)
- 📈 **What it means**: Queue backlog is growing
- 🛠️ **Action**: 
  - Reduce processing time per message
  - Increase batch size or concurrency
  - Use FIFO to sequence if order matters

### 5. `Duration` vs `Timeout`
- 📈 **What it means**: How close execution time is to your Lambda timeout
- 🛠️ **Action**: 
  - If Duration ≈ Timeout: increase `timeout`
  - If Duration is low but Timeout is high: consider reducing Timeout for cost

---

✅ Always use **CloudWatch Alarms** to notify if:
- Throttles > 0 for 5 minutes
- DLQ receives messages
- IteratorAge > threshold (e.g. 60s)


---

## 🚨 Setting Up CloudWatch Alarms

To proactively detect issues in your quiz system, configure the following CloudWatch Alarms.

### 🔔 Recommended Alarms

| Metric                        | Threshold Example              | Action                                   |
|-------------------------------|--------------------------------|------------------------------------------|
| Lambda `Throttles`           | > 0 for 5 mins                 | Increase concurrency or tune traffic     |
| Lambda `Errors`              | > 1 for 1 minute               | Check logs, validate message format      |
| Lambda `Duration`            | > 25s if timeout is 30s        | Optimize processing or increase timeout  |
| Lambda `IteratorAge`         | > 60s for 2 data points        | Increase concurrency or fix backlog      |
| SQS `ApproximateMessagesVisible` | > 100 for 5 minutes        | Indicates queue is backing up            |
| SQS `NumberOfMessagesSentToDLQ` | >= 1                         | Indicates failed message processing      |

---

### 🛠️ CDK Example: Create Alarms for Lambda

```python
from aws_cdk import aws_cloudwatch as cw

# Alarm for Lambda Throttles
cw.Alarm(self, "LambdaThrottleAlarm",
    metric=cw.Metric(
        namespace="AWS/Lambda",
        metric_name="Throttles",
        dimensions_map={"FunctionName": quizgen_fn.function_name},
        statistic="Sum",
        period=cdk.Duration.minutes(5)
    ),
    threshold=0,
    evaluation_periods=1,
    comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
    alarm_description="Lambda is throttling"
)
```

---

### 📣 Notifications (Optional)

To receive alerts:
- Create an **SNS Topic**
- Add **email subscription**
- Attach the topic to each alarm

```python
import aws_cdk.aws_sns as sns
import aws_cdk.aws_sns_subscriptions as subs

topic = sns.Topic(self, "QuizAlerts")
topic.add_subscription(subs.EmailSubscription("your-email@example.com"))

alarm.add_alarm_action(cw_actions.SnsAction(topic))
```

---

