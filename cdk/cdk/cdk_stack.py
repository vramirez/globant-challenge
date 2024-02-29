import aws_cdk as core
from constructs import Construct
from aws_cdk import (
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_rds as rds,
    aws_ec2 as ec2,
    Stack
)
class CdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        csv_bucket = s3.Bucket(self, "csvBucket", removal_policy=core.RemovalPolicy.DESTROY)
        my_vpc = ec2.Vpc(self, "MyVpc", max_azs=2)
        my_database = rds.DatabaseInstance(self, "globant_db",
        engine=rds.DatabaseInstanceEngine.mysql(
            version=rds.MysqlEngineVersion.VER_8_0_28
        ),
        instance_type=ec2.InstanceType.of(
            ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO
        ),
        vpc=my_vpc,
        #vpc_placement=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        allocated_storage=10,
        multi_az=False,
        publicly_accessible=True,
        removal_policy=core.RemovalPolicy.DESTROY,
        deletion_protection=False,
        instance_identifier="globantInstance",
        database_name="globant_db",
        credentials=rds.Credentials.from_generated_secret("globant_db_admin"),
        port=3306
    )

        lambda_reader = lambda_.Function(self, "MyLambdaFunction",
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler="lambda_read_s3.handler",  
            code=lambda_.Code.from_asset("lambdas"), 
            environment={
                # TO-DO Define environment variables here
            }
        )
        lambda_reader.add_to_role_policy(
            iam.PolicyStatement(
                actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                resources=["*"]
            )
        )
        api = apigateway.RestApi(self, "globantApi",
            rest_api_name="Globant API",
            description="An API for Globant demo"
        )

        # Define Lambda integration for API Gateway
        integration = apigateway.LambdaIntegration(lambda_reader)

        # Create API Gateway resource
        my_resource = api.root.add_resource("readFile")
        method = my_resource.add_method("GET", integration)
        #method.
        integration.request_parameters={"method.request.querystring.paramtest" : True}
        csv_bucket.grant_read(lambda_reader)


        
