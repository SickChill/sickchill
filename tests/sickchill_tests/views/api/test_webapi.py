import logging

from pytest import fixture

from sickchill.views.api import webapi


@fixture(params=set(webapi.function_mapper.values()))
def api_command(request, caplog):
    with caplog.at_level(logging.WARNING, logger="root"):
        caplog.set_level(logging.DEBUG, logger="sickchill")
        caplog.set_level(logging.WARNING, logger="cacheyou")
        caplog.set_level(logging.WARNING, logger="urllib3")
        yield request.param


def test_api_calls(api_command, capsys):
    with capsys.disabled():
        print(api_command._help)

    # TODO: test the api calls, this method will be called once for each api command automatically because of the fixture
