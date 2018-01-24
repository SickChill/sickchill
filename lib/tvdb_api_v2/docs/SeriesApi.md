# swagger_client.SeriesApi

All URIs are relative to *https://localhost/*

Method | HTTP request | Description
------------- | ------------- | -------------
[**series_id_actors_get**](SeriesApi.md#series_id_actors_get) | **GET** /series/{id}/actors | 
[**series_id_episodes_get**](SeriesApi.md#series_id_episodes_get) | **GET** /series/{id}/episodes | 
[**series_id_episodes_query_get**](SeriesApi.md#series_id_episodes_query_get) | **GET** /series/{id}/episodes/query | 
[**series_id_episodes_query_params_get**](SeriesApi.md#series_id_episodes_query_params_get) | **GET** /series/{id}/episodes/query/params | 
[**series_id_episodes_summary_get**](SeriesApi.md#series_id_episodes_summary_get) | **GET** /series/{id}/episodes/summary | 
[**series_id_filter_get**](SeriesApi.md#series_id_filter_get) | **GET** /series/{id}/filter | 
[**series_id_filter_params_get**](SeriesApi.md#series_id_filter_params_get) | **GET** /series/{id}/filter/params | 
[**series_id_get**](SeriesApi.md#series_id_get) | **GET** /series/{id} | 
[**series_id_head**](SeriesApi.md#series_id_head) | **HEAD** /series/{id} | 
[**series_id_images_get**](SeriesApi.md#series_id_images_get) | **GET** /series/{id}/images | 
[**series_id_images_query_get**](SeriesApi.md#series_id_images_query_get) | **GET** /series/{id}/images/query | 
[**series_id_images_query_params_get**](SeriesApi.md#series_id_images_query_params_get) | **GET** /series/{id}/images/query/params | 


# **series_id_actors_get**
> SeriesActors series_id_actors_get(id)



Returns actors for the given series id

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
api_instance = swagger_client.SeriesApi()
id = 789 # int | ID of the series

try: 
    api_response = api_instance.series_id_actors_get(id)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling SeriesApi->series_id_actors_get: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| ID of the series | 

### Return type

[**SeriesActors**](SeriesActors.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **series_id_episodes_get**
> SeriesEpisodes series_id_episodes_get(id, page=page)



All episodes for a given series. Paginated with 100 results per page.

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
api_instance = swagger_client.SeriesApi()
id = 789 # int | ID of the series
page = 'page_example' # str | Page of results to fetch. Defaults to page 1 if not provided. (optional)

try: 
    api_response = api_instance.series_id_episodes_get(id, page=page)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling SeriesApi->series_id_episodes_get: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| ID of the series | 
 **page** | **str**| Page of results to fetch. Defaults to page 1 if not provided. | [optional] 

### Return type

[**SeriesEpisodes**](SeriesEpisodes.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **series_id_episodes_query_get**
> SeriesEpisodesQuery series_id_episodes_query_get(id, absolute_number=absolute_number, aired_season=aired_season, aired_episode=aired_episode, dvd_season=dvd_season, dvd_episode=dvd_episode, imdb_id=imdb_id, page=page, accept_language=accept_language)



This route allows the user to query against episodes for the given series. The response is a paginated array of episode records that have been filtered down to basic information.

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
api_instance = swagger_client.SeriesApi()
id = 789 # int | ID of the series
absolute_number = 'absolute_number_example' # str | Absolute number of the episode (optional)
aired_season = 'aired_season_example' # str | Aired season number (optional)
aired_episode = 'aired_episode_example' # str | Aired episode number (optional)
dvd_season = 'dvd_season_example' # str | DVD season number (optional)
dvd_episode = 'dvd_episode_example' # str | DVD episode number (optional)
imdb_id = 'imdb_id_example' # str | IMDB id of the series (optional)
page = 'page_example' # str | Page of results to fetch. Defaults to page 1 if not provided. (optional)
accept_language = 'accept_language_example' # str | Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. (optional)

try: 
    api_response = api_instance.series_id_episodes_query_get(id, absolute_number=absolute_number, aired_season=aired_season, aired_episode=aired_episode, dvd_season=dvd_season, dvd_episode=dvd_episode, imdb_id=imdb_id, page=page, accept_language=accept_language)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling SeriesApi->series_id_episodes_query_get: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| ID of the series | 
 **absolute_number** | **str**| Absolute number of the episode | [optional] 
 **aired_season** | **str**| Aired season number | [optional] 
 **aired_episode** | **str**| Aired episode number | [optional] 
 **dvd_season** | **str**| DVD season number | [optional] 
 **dvd_episode** | **str**| DVD episode number | [optional] 
 **imdb_id** | **str**| IMDB id of the series | [optional] 
 **page** | **str**| Page of results to fetch. Defaults to page 1 if not provided. | [optional] 
 **accept_language** | **str**| Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. | [optional] 

### Return type

[**SeriesEpisodesQuery**](SeriesEpisodesQuery.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **series_id_episodes_query_params_get**
> SeriesEpisodesQueryParams series_id_episodes_query_params_get(id)



Returns the allowed query keys for the `/series/{id}/episodes/query` route

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
api_instance = swagger_client.SeriesApi()
id = 789 # int | ID of the series

try: 
    api_response = api_instance.series_id_episodes_query_params_get(id)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling SeriesApi->series_id_episodes_query_params_get: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| ID of the series | 

### Return type

[**SeriesEpisodesQueryParams**](SeriesEpisodesQueryParams.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **series_id_episodes_summary_get**
> SeriesEpisodesSummary series_id_episodes_summary_get(id)



Returns a summary of the episodes and seasons available for the series.  __Note__: Season \"0\" is for all episodes that are considered to be specials.

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
api_instance = swagger_client.SeriesApi()
id = 789 # int | ID of the series

try: 
    api_response = api_instance.series_id_episodes_summary_get(id)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling SeriesApi->series_id_episodes_summary_get: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| ID of the series | 

### Return type

[**SeriesEpisodesSummary**](SeriesEpisodesSummary.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **series_id_filter_get**
> SeriesData series_id_filter_get(id, keys, accept_language=accept_language)



Returns a series records, filtered by the supplied comma-separated list of keys. Query keys can be found at the `/series/{id}/filter/params` route.

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
api_instance = swagger_client.SeriesApi()
id = 789 # int | ID of the series
keys = 'keys_example' # str | Comma-separated list of keys to filter by
accept_language = 'accept_language_example' # str | Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. (optional)

try: 
    api_response = api_instance.series_id_filter_get(id, keys, accept_language=accept_language)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling SeriesApi->series_id_filter_get: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| ID of the series | 
 **keys** | **str**| Comma-separated list of keys to filter by | 
 **accept_language** | **str**| Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. | [optional] 

### Return type

[**SeriesData**](SeriesData.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **series_id_filter_params_get**
> FilterKeys series_id_filter_params_get(id, accept_language=accept_language)



Returns the list of keys available for the `/series/{id}/filter` route

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
api_instance = swagger_client.SeriesApi()
id = 789 # int | ID of the series
accept_language = 'accept_language_example' # str | Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. (optional)

try: 
    api_response = api_instance.series_id_filter_params_get(id, accept_language=accept_language)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling SeriesApi->series_id_filter_params_get: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| ID of the series | 
 **accept_language** | **str**| Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. | [optional] 

### Return type

[**FilterKeys**](FilterKeys.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **series_id_get**
> SeriesData series_id_get(id, accept_language=accept_language)



Returns a series records that contains all information known about a particular series id.

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
api_instance = swagger_client.SeriesApi()
id = 789 # int | ID of the series
accept_language = 'accept_language_example' # str | Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. (optional)

try: 
    api_response = api_instance.series_id_get(id, accept_language=accept_language)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling SeriesApi->series_id_get: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| ID of the series | 
 **accept_language** | **str**| Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. | [optional] 

### Return type

[**SeriesData**](SeriesData.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **series_id_head**
> series_id_head(id, accept_language=accept_language)



Returns header information only about the given series ID.

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
api_instance = swagger_client.SeriesApi()
id = 789 # int | ID of the series
accept_language = 'accept_language_example' # str | Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. (optional)

try: 
    api_instance.series_id_head(id, accept_language=accept_language)
except ApiException as e:
    print "Exception when calling SeriesApi->series_id_head: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| ID of the series | 
 **accept_language** | **str**| Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. | [optional] 

### Return type

void (empty response body)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **series_id_images_get**
> SeriesImagesCounts series_id_images_get(id, accept_language=accept_language)



Returns a summary of the images for a particular series

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
api_instance = swagger_client.SeriesApi()
id = 789 # int | ID of the series
accept_language = 'accept_language_example' # str | Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. (optional)

try: 
    api_response = api_instance.series_id_images_get(id, accept_language=accept_language)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling SeriesApi->series_id_images_get: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| ID of the series | 
 **accept_language** | **str**| Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. | [optional] 

### Return type

[**SeriesImagesCounts**](SeriesImagesCounts.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **series_id_images_query_get**
> SeriesImageQueryResults series_id_images_query_get(id, key_type=key_type, resolution=resolution, sub_key=sub_key, accept_language=accept_language)



Query images for the given series ID.

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
api_instance = swagger_client.SeriesApi()
id = 789 # int | ID of the series
key_type = 'key_type_example' # str | Type of image you're querying for (fanart, poster, etc. See ../images/query/params for more details). (optional)
resolution = 'resolution_example' # str | Resolution to filter by (1280x1024, for example) (optional)
sub_key = 'sub_key_example' # str | Subkey for the above query keys. See /series/{id}/images/query/params for more information (optional)
accept_language = 'accept_language_example' # str | Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. (optional)

try: 
    api_response = api_instance.series_id_images_query_get(id, key_type=key_type, resolution=resolution, sub_key=sub_key, accept_language=accept_language)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling SeriesApi->series_id_images_query_get: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| ID of the series | 
 **key_type** | **str**| Type of image you&#39;re querying for (fanart, poster, etc. See ../images/query/params for more details). | [optional] 
 **resolution** | **str**| Resolution to filter by (1280x1024, for example) | [optional] 
 **sub_key** | **str**| Subkey for the above query keys. See /series/{id}/images/query/params for more information | [optional] 
 **accept_language** | **str**| Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. | [optional] 

### Return type

[**SeriesImageQueryResults**](SeriesImageQueryResults.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **series_id_images_query_params_get**
> SeriesImagesQueryParams series_id_images_query_params_get(id, accept_language=accept_language)



Returns the allowed query keys for the `/series/{id}/images/query` route. Contains a parameter record for each unique `keyType`, listing values that will return results.

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
api_instance = swagger_client.SeriesApi()
id = 789 # int | ID of the series
accept_language = 'accept_language_example' # str | Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. (optional)

try: 
    api_response = api_instance.series_id_images_query_params_get(id, accept_language=accept_language)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling SeriesApi->series_id_images_query_params_get: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| ID of the series | 
 **accept_language** | **str**| Records are returned with the Episode name and Overview in the desired language, if it exists. If there is no translation for the given language, then the record is still returned but with empty values for the translated fields. | [optional] 

### Return type

[**SeriesImagesQueryParams**](SeriesImagesQueryParams.md)

### Authorization

[jwtToken](../README.md#jwtToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

