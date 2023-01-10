from aws_cdk import Stack
from aws_cdk.aws_ec2 import Vpc
import aws_cdk.aws_sqs as sqs
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_ecr as ecr
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ecs_patterns as ecs_patterns
import aws_cdk.aws_autoscaling as autoscaling
import aws_cdk.aws_applicationautoscaling as app_autoscaling
import aws_cdk.aws_opensearchservice as opensearch

class WhisperServerECSStack(Stack):
    def __init__(
        self, scope, id,
        ecr_repo: ecr.Repository,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        account_id = Stack.of(self).account
        region = Stack.of(self).region

        # use default vpc for now
        self.vpc = Vpc.from_lookup(self, "VPC", is_default=True)

        self.task_result_bucket = s3.Bucket(self, "whisper-server-task-results")

        self.celery_queue = sqs.Queue(self, "whisper-server-celery-queue")

        self.realtime_queue = sqs.Queue(self, "whisper-server-realtime-queue")

        self.slow_queue = sqs.Queue(self, "whisper-server-slow-queue")

        self.opensearch_domain = opensearch.Domain(
            self, "whisper-server-search-domain",
            version=opensearch.EngineVersion.open_search('2.3'),
            ebs=opensearch.EbsOptions(
                volume_size=100,
                volume_type=ec2.EbsDeviceVolumeType.GP3
            ),
            capacity=opensearch.CapacityConfig(
                data_nodes=1,
                data_node_instance_type='t3.small.search',
            ),
        )

        self.cluster = ecs.Cluster(self, "whisper-server-cluster", vpc=self.vpc)

        self.cluster.enable_fargate_capacity_providers()

        environment = {
            "AWS_REGION": region,
            "BROKER_URL": "sqs://",
            "BACKEND_URL": "s3://" + self.task_result_bucket.bucket_name,
            "S3_BUCKET": self.task_result_bucket.bucket_name,
            "CELERY_QUEUE_URL": self.celery_queue.queue_url,
            "REALTIME_QUEUE_URL": self.realtime_queue.queue_url,
            "SLOW_QUEUE_URL": self.slow_queue.queue_url,
            "OPENSEARCH_HOST": self.opensearch_domain.domain_endpoint,
        }

        self.realtime_service = ecs_patterns.QueueProcessingFargateService(
            self, "whisper-realtime",
            cluster=self.cluster,
            assign_public_ip=True,
            cpu=1024,
            memory_limit_mib=4096,
            image=ecs.ContainerImage.from_ecr_repository(ecr_repo, tag='latest'),
            command=["celery", "-A", "realtime_tasks", "worker", "-l", "info", "-Q", "celery,whisper-realtime"],
            environment=environment,
            queue=self.realtime_queue,
            capacity_provider_strategies=[
                ecs.CapacityProviderStrategy(
                    capacity_provider="FARGATE",
                    weight=1
                ),
                ecs.CapacityProviderStrategy(
                    capacity_provider="FARGATE_SPOT",
                    weight=0
                ),
            ],
            scaling_steps=[
                app_autoscaling.ScalingInterval(
                    upper=0,
                    change=-1,
                ),
                app_autoscaling.ScalingInterval(
                    lower=1,
                    change=1,
                ),
                # app_autoscaling.ScalingInterval(
                #     lower=50,
                #     change=1,
                # ),
            ],
            min_scaling_capacity=1,
            max_scaling_capacity=1,
        )

        auto_scaling_group = autoscaling.AutoScalingGroup(
            self, "whisper-gpu-asg",
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(hardware_type=ecs.AmiHardwareType.GPU),
            # instance_type=ec2.InstanceType("g5.xlarge"),
            instance_type=ec2.InstanceType("g4dn.xlarge"),
            block_devices=[
                autoscaling.BlockDevice(
                    device_name="/dev/xvda",
                    volume=autoscaling.BlockDeviceVolume.ebs(
                        100,
                        volume_type=autoscaling.EbsDeviceVolumeType.GP3,
                        delete_on_termination=True,
                    ),
                )
            ],
            vpc=self.vpc,
            min_capacity=0,
            max_capacity=1,
        )

        capacity_provider = ecs.AsgCapacityProvider(
            self, "whisper-gpu-asg-capacity-provider",
            auto_scaling_group=auto_scaling_group,
        )

        self.cluster.add_asg_capacity_provider(capacity_provider)

        self.slow_service = ecs_patterns.QueueProcessingEc2Service(
            self, "whisper-slow",
            cluster=self.cluster,
            gpu_count=1,
            cpu=4096,
            # memory_limit_mib=15360,
            memory_reservation_mib=15360,
            image=ecs.ContainerImage.from_ecr_repository(ecr_repo, tag='latest'),
            command=["celery", "-A", "slow_tasks", "worker", "-l", "info", "-Q", "celery,whisper-slow", "-P", "solo"],
            environment=environment,
            queue=self.slow_queue,
            capacity_provider_strategies=[
                ecs.CapacityProviderStrategy(
                    capacity_provider=capacity_provider.capacity_provider_name,
                    weight=1,
                ),
            ],
            scaling_steps=[
                app_autoscaling.ScalingInterval(
                    upper=0,
                    change=-1,
                ),
                app_autoscaling.ScalingInterval(
                    lower=1,
                    change=1,
                ),
                # app_autoscaling.ScalingInterval(
                #     lower=50,
                #     change=1,
                # ),
            ],
            min_scaling_capacity=1,
            max_scaling_capacity=1,
        )

        self.celery_queue.grant_send_messages(self.realtime_service.task_definition.task_role)
        self.celery_queue.grant_send_messages(self.slow_service.task_definition.task_role)
        self.celery_queue.grant_consume_messages(self.realtime_service.task_definition.task_role)
        self.celery_queue.grant_consume_messages(self.slow_service.task_definition.task_role)

        # allow real-time task to send messages to the slow queue
        self.slow_queue.grant_send_messages(self.realtime_service.task_definition.task_role)

        self.task_result_bucket.grant_read_write(self.realtime_service.task_definition.task_role)
        self.task_result_bucket.grant_read_write(self.slow_service.task_definition.task_role)

        self.opensearch_domain.grant_read_write(self.slow_service.task_definition.task_role)
