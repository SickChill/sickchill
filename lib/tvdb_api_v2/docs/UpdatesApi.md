# swagger_client.UpdatesApi

All URIs are relative to *https://localhost/*

Method | HTTP request | Description
------------- | ------------- | -------------
[**updated_query_get**](UpdatesApi.md#updated_query_get) | **GET** /updated/query | 
[**updated_query_params_get**](UpdatesApi.md#updated_query_params_get) | **GET** /updated/query/params | 


# **updated_query_get**
> UpdateData updated_query_get(from_time, to_time=to_time, accept_language=accept_language)



Returns an array of series that have changed in a maximum of one week blocks since the provided `fromTime`.   The user may specify a `toTime` to grab results for less than a week. Any timespan larger than a week will be reduced down to one week automatically.

### Example 
```python
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure API key authorization: jwtToken
swagger_client.configuration.api_key['Authorization'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# swagger_client.configuration.api_key_prefix['Authorization'] = 'Bearer'

# create an instance of the API class
api_instance = swagger_client.UpdatesApi()
from_time = 'from_time_example' # str | Epoch time to start your date range.
to_time = 'to_time_example' # str | Epoch time to end your date range. Must be one week from `fromTime`. (optional)
accept_language = 'accept_language_example' # str | Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. (optional)

try: 
    api_response = api_instance.updated_query_get(from_time, to_time=to_time, accept_language=accept_language)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling UpdatesApi->updated_query_get: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **from_time** | **str**| Epoch time to start your date range. | 
 **to_time** | **str**| Epoch time to end your date range. Must be one week from &#x60;fromTime&#x60;. | [optional] 
 **accept_language** | **str**| Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. | [optional] 

### Return type

[**UpdateData**](UpdateData.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **updated_query_params_get**
> UpdateDataQueryParams updated_query_params_get()



Returns an array of valid query keys for the `/updated/query/params` route.

### Example 
```python
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure API key authorization: jwtToken
swagger_client.configuration.api_key['Authorization'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# swagger_client.configuration.api_key_prefix['Authorization'] = 'Bearer'

# create an instance of the API class
api_instance = swagger_client.UpdatesApi()

try: 
    api_response = api_instance.updated_query_params_get()
    pprint(api_response)
except ApiException as e:
    print "Exception when calling UpdatesApi->updated_query_params_get: %s\n" % e
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**UpdateDataQueryParams**](UpdateDataQueryParams.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

