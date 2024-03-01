# globant-challenge
Globant challenge for applying as Data Engineer

## Made with AWS CDK

Deploys:
- Amazon S3 to store the CSV before processing
- AWS Lambda in Python to process file
- Amazon RDS MySQL to store the rows 
- API Gateway to communicate with the Lambda
- VPC for networking

The Lambda thru the API Gateway reads from S3 and insert into the database on the required table, depending upon the batch_size parameter.


# Setup

After configuring your AWS environment locally and installing docker, run

`cd cdk`
`python -m venv .venv`
`source .venv/bin/activate`
`cdk deploy`