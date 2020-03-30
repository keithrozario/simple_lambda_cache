from aws_lambda_cache import __version__
from aws_lambda_cache import ssm_cache

import time
import pytest
from botocore.exceptions import ClientError

from tests.variables_data import *
from tests.helper_functions import update_parameter


def test_initialize():
    assert __version__ == '0.2.5'
    update_parameter(ssm_parameter, ssm_parameter_value)
    update_parameter(ssm_parameter_2, ssm_parameter_2_value)
    update_parameter(secure_parameter, secure_parameter_value, param_type='SecureString')
    update_parameter(long_name_parameter, long_name_value)

# Test Non-existent parameter

@ssm_cache(parameter="/some/nonexist/parameter")
def parameter_not_exist_var_handler(event, context):
    return event

def test_non_existing_parameter():
    
    test_event = {'event_name': 'test'}
    test_context = {}
    with pytest.raises(ClientError) as e:
        event = parameter_not_exist_var_handler(test_event, test_context)
        assert e['Error']['Code'] == "ParameterNotFound"


# Test parameter import and stacking
@ssm_cache(parameter=ssm_parameter)
def single_var_handler(event, context):
    return event

@ssm_cache(parameter=ssm_parameter)
@ssm_cache(parameter=ssm_parameter_2)
def double_var_handler(event, context):
    return event


@ssm_cache(parameter=long_name_parameter)
def long_name_var_handler(event,context):
    return event

def test_var_handlers():

    test_event = {'event_name': 'test'}
    test_context = {}

    event = single_var_handler(test_event, test_context)
    assert event.get(ssm_parameter_default_name) == ssm_parameter_value
    
    event = double_var_handler(test_event, test_context)
    assert event.get(ssm_parameter_default_name) == ssm_parameter_value
    assert event.get(ssm_parameter_2_default_name) == ssm_parameter_2_value

    event = long_name_var_handler(test_event, test_context)
    assert event.get(long_name_default_name) == long_name_value


# Test Parameter Caching TTL settings
@ssm_cache(parameter=ssm_parameter, ttl_seconds=5)
def five_second_ttl(event, context):
    return event

def test_cache():
    
    updated_value = 'Dummy Value NEW!!'

    test_event = {'event_name': 'test'}
    test_context = {}

    event = five_second_ttl(test_event, test_context)
    assert event.get(ssm_parameter_default_name) == ssm_parameter_value
    
    # Update parameter but call before 5 seconds
    update_parameter(ssm_parameter, updated_value)
    event = five_second_ttl(test_event, test_context)
    assert event.get(ssm_parameter_default_name) == ssm_parameter_value

    # Wait 5 seconds call again
    time.sleep(5)
    event = five_second_ttl(test_event, test_context)
    assert event.get(ssm_parameter_default_name) == updated_value

    # Revert back to normal
    update_parameter(ssm_parameter, ssm_parameter_value)
    time.sleep(5)
    event = five_second_ttl(test_event, test_context)
    assert event.get(ssm_parameter_default_name) == ssm_parameter_value

# Test Parameter Rename
@ssm_cache(parameter=ssm_parameter, var_name=ssm_parameter_replaced_var_name)
def renamed_var(event, context):
    return event

def test_rename_parameter():

    test_event = {'event_name': 'test'}
    test_context = {}

    event = renamed_var(test_event, test_context)
    assert event.get(ssm_parameter_replaced_var_name) == ssm_parameter_value

# Test Secure String import
@ssm_cache(parameter=secure_parameter)
def secure_var_handler(event,context):
    return event

def test_secure_string():

    test_event = {'event_name': 'test'}
    test_context = {}

    event = secure_var_handler(test_event, test_context)
    assert event.get(secure_parameter_default_name) == secure_parameter_value

# Test ttl_seconds=0 settings, no cache
@ssm_cache(parameter=ssm_parameter, ttl_seconds=0)
def no_cache(event, context):
    return event

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
