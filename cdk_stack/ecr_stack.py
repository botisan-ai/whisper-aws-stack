from aws_cdk import Stack
import aws_cdk.aws_ecr as ecr

class CeleryTasksECRStack(Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        ecr.Repository(self, id, repository_name="redis")
        ecr.Repository(self, id, repository_name="whisper-server")

