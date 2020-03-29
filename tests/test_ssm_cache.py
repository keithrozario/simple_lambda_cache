from aws_lambda_cache import __version__
from aws_lambda_cache import ssm_cache

import time

import boto3

ssm_parameter = "/test/something"
ssm_parameter_value = "Dummy Value 1"
ssm_parameter_default_name = "_test_something"
ssm_parameter_replaced_var_name = "variable_1"

ssm_parameter_2 = "/test/something_else"
ssm_parameter_2_value = "Dummy Value 2"
ssm_parameter_2_default_name = "_test_something_else"

secure_parameter = "/test/secure/something"
secure_parameter_value = "This is secure"
secure_parameter_default_name = "_test_secure_something"


@ssm_cache(parameter=ssm_parameter)
@ssm_cache(parameter=ssm_parameter_2)
def double_var_handler(event, context):
    return event

@ssm_cache(parameter=ssm_parameter)
def single_var_handler(event, context):
    return event

@ssm_cache(parameter=ssm_parameter, ttl_seconds=5)
def five_second_ttl(event, context):
    return event

@ssm_cache(parameter=ssm_parameter, ttl_seconds=0)
def no_cache(event, context):
    return event

@ssm_cache(parameter=ssm_parameter, var_name=ssm_parameter_replaced_var_name)
def renamed_var(event, context):
    return event

def update_parameter(parameter, value):
    """
    Updates parameter to new value
    """
    ssm_client = boto3.client('ssm')
    response = ssm_client.put_parameter(
        Name=parameter,
        Value=value,
        Type='String',
        Overwrite=True,
        Tier='Standard'
        )
    return

def update_secure_parameter(parameter, value):
    """
    Updates parameter to new value
    """
    ssm_client = boto3.client('ssm')
    response = ssm_client.put_parameter(
        Name=parameter,
        Value=value,
        Type='String',
        Overwrite=True,
        Tier='Standard'
        )
    return 

def test_initialize():
    assert __version__ == '0.2.5'
    update_parameter(ssm_parameter, ssm_parameter_value)
    update_parameter(ssm_parameter_2, ssm_parameter_2_value)

def test_var_handlers():

    test_event = {'event_name': 'test'}
    test_context = {}

    event = single_var_handler(test_event, test_context)
    assert event.get('_test_something') == ssm_parameter_value
    
    event = double_var_handler(test_event, test_context)
    assert event.get('_test_something') == ssm_parameter_value
    assert event.get('_test_something_else') == ssm_parameter_2_value

def test_cache():
    
    updated_value = 'Dummy Value NEW!!'

    test_event = {'event_name': 'test'}
    test_context = {}

    event = five_second_ttl(test_event, test_context)
    assert event.get('_test_something') == ssm_parameter_value
    
    # Update parameter but call before 5 seconds
    update_parameter(ssm_parameter, updated_value)
    event = five_second_ttl(test_event, test_context)
    assert event.get('_test_something') == ssm_parameter_value

    # Wait 5 seconds call again
    time.sleep(5)
    event = five_second_ttl(test_event, test_context)
    assert event.get('_test_something') == updated_value

    # Revert back to normal
    update_parameter(ssm_parameter, ssm_parameter_value)
    time.sleep(5)
    event = five_second_ttl(test_event, test_context)
    assert event.get('_test_something') == ssm_parameter_value

def test_rename_parameter():

    test_event = {'event_name': 'test'}
    test_context = {}

    event = renamed_var(test_event, test_context)
    assert event.get(ssm_parameter_replaced_var_name) == ssm_parameter_value

def test_secure_string():

    test_event = {'event_name': 'test'}
    test_context = {}

    event = renamed_var(test_event, test_context)
    assert event.get(ssm_parameter_replaced_var_name) == ssm_parameter_value

def test_no_cache():
    test_event = {'event_name': 'test'}
    test_context = {}
    new_value = "New Value"

    event = no_cache(test_event, test_context)
    assert event.get(ssm_parameter_default_name) == ssm_parameter_value
    
    update_parameter(ssm_parameter, new_value)
    event = no_cache(test_event, test_context)
    assert event.get(ssm_parameter_default_name) == new_value

    update_parameter(ssm_parameter, ssm_parameter_value)
    event = no_cache(test_event, test_context)
    assert event.get(ssm_parameter_default_name) == ssm_parameter_value