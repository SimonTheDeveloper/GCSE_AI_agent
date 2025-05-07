from aws_cdk import Stack
import aws_cdk.aws_dynamodb as dynamodb
from constructs import Construct
from dotenv import load_dotenv

class AirlineTestStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        table = dynamodb.Table(
            self, "FlightsTable",
            partition_key=dynamodb.Attribute(name="flight_id", type=dynamodb.AttributeType.STRING),
            table_name="FlightsTable"  # Set custom table name
        )