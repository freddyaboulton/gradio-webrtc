When deploying in cloud environments with firewalls (like Hugging Face Spaces, RunPod), your WebRTC connections may be blocked from making direct connections. In these cases, you need a TURN server to relay the audio/video traffic between users. This guide covers different options for setting up FastRTC to connect to a TURN server.

!!! tip
    The `rtc_configuration` parameter of the `Stream` class also be passed to the [`WebRTC`](userguide/gradio) component directly if you're building a standalone gradio app.

## Community Server

Hugging Face graciously provides a TURN server for the community.
In order to use it, you need to first create a Hugging Face account by going to [huggingface.co](https://huggingface.co/).

Then navigate to this [space](https://huggingface.co/spaces/fastrtc/turn-server-login) and follow the instructions on the page. You just have to click the "Log in" button and then the "Sign Up" button.

![turn_login](https://github.com/user-attachments/assets/cefa8dec-487e-47d8-bb96-1a14a701f6e5)

Then you can use the `get_hf_turn_credentials` helper to get your credentials:

```python
from fastrtc import get_hf_turn_credentials, Stream

# Pass a valid access token for your Hugging Face account
# or set the HF_TOKEN environment variable 
credentials = get_hf_turn_credentials(token=None)

Stream(
    handler=...,
    rtc_configuration=credentials,
    modality="audio",
    mode="send-receive"
)
```

!!! warning

    This is a shared resource so we make no latency/availability guarantees.
    For more robust options, see the Twilio and self-hosting options below.


## Twilio API

The easiest way to do this is to use a service like Twilio.

Create a **free** [account](https://login.twilio.com/u/signup) and the install the `twilio` package with pip (`pip install twilio`). You can then connect from the WebRTC component like so:

```python
from fastrtc import Stream
from twilio.rest import Client
import os

account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

client = Client(account_sid, auth_token)

token = client.tokens.create()

rtc_configuration = {
    "iceServers": token.ice_servers,
    "iceTransportPolicy": "relay",
}

Stream(
    handler=...,
    rtc_configuration=rtc_configuration,
    modality="audio",
    mode="send-receive"
)
```

!!! tip "Automatic login"

    You can log in automatically with the `get_twilio_turn_credentials` helper

    ```python
    from gradio_webrtc import get_twilio_turn_credentials

    # Will automatically read the TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
    # env variables but you can also pass in the tokens as parameters
    rtc_configuration = get_twilio_turn_credentials()
    ```

## Self Hosting

We have developed a script that can automatically deploy a TURN server to Amazon Web Services (AWS). You can follow the instructions [here](https://github.com/freddyaboulton/turn-server-deploy) or this guide.

### Prerequisites

Clone the following [repository](https://github.com/freddyaboulton/turn-server-deploy) and install the `aws` cli if you have not done so already (`pip install awscli`).

Log into your AWS account and create an IAM user with the following permissions:

- [AWSCloudFormationFullAccess](https://us-east-1.console.aws.amazon.com/iam/home?region=us-east-1#/policies/details/arn%3Aaws%3Aiam%3A%3Aaws%3Apolicy%2FAWSCloudFormationFullAccess)
- [AmazonEC2FullAccess](https://us-east-1.console.aws.amazon.com/iam/home?region=us-east-1#/policies/details/arn%3Aaws%3Aiam%3A%3Aaws%3Apolicy%2FAmazonEC2FullAccess)


Create a key pair for this user and write down the "access key" and "secret access key". Then log into the aws cli with these credentials (`aws configure`).

Finally, create an ec2 keypair (replace `your-key-name` with the name you want to give it).

```
aws ec2 create-key-pair --key-name your-key-name --query 'KeyMaterial' --output text > your-key-name.pem
```

### Running the script

Open the `parameters.json` file and fill in the correct values for all the parameters:

- `KeyName`: The key file we just created, e.g. `your-key-name` (omit `.pem`).
- `TurnUserName`: The username needed to connect to the server.
- `TurnPassword`: The password needed to connect to the server.
- `InstanceType`: One of the following values `t3.micro`, `t3.small`, `t3.medium`, `c4.large`, `c5.large`.


Then run the deployment script:

```bash
aws cloudformation create-stack \
  --stack-name turn-server \
  --template-body file://deployment.yml \
  --parameters file://parameters.json \
  --capabilities CAPABILITY_IAM
```

You can then wait for the stack to come up with:

```bash
aws cloudformation wait stack-create-complete \
  --stack-name turn-server
```

Next, grab your EC2 server's public ip with:

```
aws cloudformation describe-stacks \
  --stack-name turn-server \
  --query 'Stacks[0].Outputs' > server-info.json
```

The `server-info.json` file will have the server's public IP and public DNS:

```json
[
    {
        "OutputKey": "PublicIP",
        "OutputValue": "35.173.254.80",
        "Description": "Public IP address of the TURN server"
    },
    {
        "OutputKey": "PublicDNS",
        "OutputValue": "ec2-35-173-254-80.compute-1.amazonaws.com",
        "Description": "Public DNS name of the TURN server"
    }
]
```

Finally, you can connect to your EC2 server from the gradio WebRTC component via the `rtc_configuration` argument:

```python
from fastrtc import Stream
rtc_configuration = {
    "iceServers": [
        {
            "urls": "turn:35.173.254.80:80",
            "username": "<my-username>",
            "credential": "<my-password>"
        },
    ]
}
Stream(
    handler=...,
    rtc_configuration=rtc_configuration,
    modality="audio",
    mode="send-receive"
)
```
