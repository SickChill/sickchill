# swagger_client.UsersApi

All URIs are relative to *https://localhost/*

Method | HTTP request | Description
------------- | ------------- | -------------
[**user_favorites_get**](UsersApi.md#user_favorites_get) | **GET** /user/favorites | 
[**user_favorites_id_delete**](UsersApi.md#user_favorites_id_delete) | **DELETE** /user/favorites/{id} | 
[**user_favorites_id_put**](UsersApi.md#user_favorites_id_put) | **PUT** /user/favorites/{id} | 
[**user_get**](UsersApi.md#user_get) | **GET** /user | 
[**user_ratings_get**](UsersApi.md#user_ratings_get) | **GET** /user/ratings | 
[**user_ratings_item_type_item_id_delete**](UsersApi.md#user_ratings_item_type_item_id_delete) | **DELETE** /user/ratings/{itemType}/{itemId} | 
[**user_ratings_item_type_item_id_item_rating_put**](UsersApi.md#user_ratings_item_type_item_id_item_rating_put) | **PUT** /user/ratings/{itemType}/{itemId}/{itemRating} | 
[**user_ratings_query_get**](UsersApi.md#user_ratings_query_get) | **GET** /user/ratings/query | 
[**user_ratings_query_params_get**](UsersApi.md#user_ratings_query_params_get) | **GET** /user/ratings/query/params | 


# **user_favorites_get**
> UserFavoritesData user_favorites_get()



Returns an array of favorite series for a given user, will be a blank array if no favorites exist.

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
api_instance = swagger_client.UsersApi()

try: 
    api_response = api_instance.user_favorites_get()
    pprint(api_response)
except ApiException as e:
    print "Exception when calling UsersApi->user_favorites_get: %s\n" % e
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**UserFavoritesData**](UserFavoritesData.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **user_favorites_id_delete**
> UserFavoritesData user_favorites_id_delete(id)



Deletes the given series ID from the user’s favorite’s list and returns the updated list.

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
api_instance = swagger_client.UsersApi()
id = 789 # int | ID of the series

try: 
    api_response = api_instance.user_favorites_id_delete(id)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling UsersApi->user_favorites_id_delete: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| ID of the series | 

### Return type

[**UserFavoritesData**](UserFavoritesData.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **user_favorites_id_put**
> UserFavoritesData user_favorites_id_put(id)



Adds the supplied series ID to the user’s favorite’s list and returns the updated list.

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
api_instance = swagger_client.UsersApi()
id = 789 # int | ID of the series

try: 
    api_response = api_instance.user_favorites_id_put(id)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling UsersApi->user_favorites_id_put: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| ID of the series | 

### Return type

[**UserFavoritesData**](UserFavoritesData.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **user_get**
> UserData user_get()



Returns basic information about the currently authenticated user.

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
api_instance = swagger_client.UsersApi()

try: 
    api_response = api_instance.user_get()
    pprint(api_response)
except ApiException as e:
    print "Exception when calling UsersApi->user_get: %s\n" % e
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**UserData**](UserData.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **user_ratings_get**
> UserRatingsData user_ratings_get()



Returns an array of ratings for the given user.

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
api_instance = swagger_client.UsersApi()

try: 
    api_response = api_instance.user_ratings_get()
    pprint(api_response)
except ApiException as e:
    print "Exception when calling UsersApi->user_ratings_get: %s\n" % e
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**UserRatingsData**](UserRatingsData.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **user_ratings_item_type_item_id_delete**
> UserRatingsDataNoLinksEmptyArray user_ratings_item_type_item_id_delete(item_type, item_id)



This route deletes a given rating of a given type.

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
api_instance = swagger_client.UsersApi()
item_type = 'item_type_example' # str | Item to update. Can be either 'series', 'episode', or 'image'
item_id = 789 # int | ID of the ratings record that you wish to modify

try: 
    api_response = api_instance.user_ratings_item_type_item_id_delete(item_type, item_id)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling UsersApi->user_ratings_item_type_item_id_delete: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **item_type** | **str**| Item to update. Can be either &#39;series&#39;, &#39;episode&#39;, or &#39;image&#39; | 
 **item_id** | **int**| ID of the ratings record that you wish to modify | 

### Return type

[**UserRatingsDataNoLinksEmptyArray**](UserRatingsDataNoLinksEmptyArray.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **user_ratings_item_type_item_id_item_rating_put**
> UserRatingsDataNoLinks user_ratings_item_type_item_id_item_rating_put(item_type, item_id, item_rating)



This route updates a given rating of a given type.

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
api_instance = swagger_client.UsersApi()
item_type = 'item_type_example' # str | Item to update. Can be either 'series', 'episode', or 'image'
item_id = 789 # int | ID of the ratings record that you wish to modify
item_rating = 789 # int | The updated rating number

try: 
    api_response = api_instance.user_ratings_item_type_item_id_item_rating_put(item_type, item_id, item_rating)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling UsersApi->user_ratings_item_type_item_id_item_rating_put: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **item_type** | **str**| Item to update. Can be either &#39;series&#39;, &#39;episode&#39;, or &#39;image&#39; | 
 **item_id** | **int**| ID of the ratings record that you wish to modify | 
 **item_rating** | **int**| The updated rating number | 

### Return type

[**UserRatingsDataNoLinks**](UserRatingsDataNoLinks.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **user_ratings_query_get**
> UserRatingsData user_ratings_query_get(item_type=item_type)



Returns an array of ratings for a given user that match the query.

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
api_instance = swagger_client.UsersApi()
item_type = 'item_type_example' # str | Item to query. Can be either 'series', 'episode', or 'banner' (optional)

try: 
    api_response = api_instance.user_ratings_query_get(item_type=item_type)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling UsersApi->user_ratings_query_get: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **item_type** | **str**| Item to query. Can be either &#39;series&#39;, &#39;episode&#39;, or &#39;banner&#39; | [optional] 

### Return type

[**UserRatingsData**](UserRatingsData.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **user_ratings_query_params_get**
> UserRatingsQueryParams user_ratings_query_params_get()



Returns a list of query params for use in the `/user/ratings/query` route.

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
api_instance = swagger_client.UsersApi()

try: 
    api_response = api_instance.user_ratings_query_params_get()
    pprint(api_response)
except ApiException as e:
    print "Exception when calling UsersApi->user_ratings_query_params_get: %s\n" % e
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**UserRatingsQueryParams**](UserRatingsQueryParams.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

