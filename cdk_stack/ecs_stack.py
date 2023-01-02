from aws_cdk import Stack
from aws_cdk.aws_ec2 import Vpc
import aws_cdk.aws_sqs as sqs
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_ecr as ecr
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_ecs_patterns as ecs_patterns
import aws_cdk.aws_applicationautoscaling as autoscaling

class WhisperServerECSStack(Stack):
    def __init__(self, scope, id, ecr_repo: ecr.Repository, **kwargs):
        super().__init__(scope, id, **kwargs)

        account_id = Stack.of(self).account
        region = Stack.of(self).region

        # use default vpc for now
        self.vpc = Vpc.from_lookup(self, "VPC", is_default=True)

        self.task_result_bucket = s3.Bucket(self, "whisper-server-task-results")

        self.celery_queue = sqs.Queue(self, "whisper-server-celery-queue")

        self.realtime_queue = sqs.Queue(self, "whisper-server-realtime-queue")

        self.slow_queue = sqs.Queue(self, "whisper-server-slow-queue")

        self.cluster = ecs.Cluster(self, "whisper-server-cluster", vpc=self.vpc)

        self.cluster.enable_fargate_capacity_providers()

        self.realtime_service = ecs_patterns.QueueProcessingFargateService(
            self, "whisper-realtime",
            cluster=self.cluster,
            assign_public_ip=True,
            cpu=1024,
            memory_limit_mib=4096,
            image=ecs.ContainerImage.from_ecr_repository(ecr_repo, tag='latest'),
            command=["celery", "-A", "realtime_tasks", "worker", "-l", "info", "-Q", "celery,whisper-realtime"],
            environment={
                "AWS_REGION": region,
                "BROKER_URL": "sqs://",
                "BACKEND_URL": "s3://" + self.task_result_bucket.bucket_name,
                "S3_BUCKET": self.task_result_bucket.bucket_name,
                "CELERY_QUEUE_URL": self.celery_queue.queue_url,
                "REALTIME_QUEUE_URL": self.realtime_queue.queue_url,
                "SLOW_QUEUE_URL": self.slow_queue.queue_url,
            },
            queue=self.realtime_queue,
            capacity_provider_strategies=[
                ecs.CapacityProviderStrategy(
                    capacity_provider="FARGATE_SPOT",
                    weight=2
                ),
                ecs.CapacityProviderStrategy(
                    capacity_provider="FARGATE",
                    weight=1
                )
            ],
            scaling_steps=[
                autoscaling.ScalingInterval(
                    upper=0,
                    change=-1,
                ),
                autoscaling.ScalingInterval(
                    lower=1,
                    change=1,
                ),
                autoscaling.ScalingInterval(
                    lower=50,
                    change=1,
                ),
            ],
            min_scaling_capacity=0,
            max_scaling_capacity=2,
        )

        self.celery_queue.grant_consume_messages(self.realtime_service.task_definition.task_role)
        self.task_result_bucket.grant_read_write(self.realtime_service.task_definition.task_role)
