from aws_cdk import App

from .ecr_stack import CeleryTasksECRStack

app = App()

ecr_stack = CeleryTasksECRStack(app, "celery-tasks-ecr-stack")

app.synth()
