from aws_cdk import App

from .ecr_stack import WhisperServerECRStack
from .ecs_stack import WhisperServerECSStack

app = App()

ecr_stack = WhisperServerECRStack(app, "whisper-server-ecr")
ecs_stack = WhisperServerECSStack(
    app, "whisper-server-ecs",
    env={
        "account": '168126166438',
        "region": 'us-west-2',
    },
    ecr_repo=ecr_stack.ecr_repo,
)

app.synth()
