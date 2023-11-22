import json

import requests


class RestApiHandler:
    default_headers = {"Content-Type": "application/json",
                       "Accept": "application/json"}

    base_url = "http://{}:{}"

    """""
    get of from server by affected_line id
    """

    @staticmethod
    def get_of_by_line_id(host, port, line_id, headers=None):

        if headers is None:
            headers = RestApiHandler.default_headers

        url = RestApiHandler.base_url.format(host, port)
        request_url = "{}api/listen_on_postprocessing_shopfloordata/byLineId/{}"\
            .format(url, str(line_id))

        response = requests.get(url=request_url, timeout=30, headers=headers)
        if response.status_code == 200:
            return json.loads(response.content)

    @staticmethod
    def get_line_by_line_id(host, port, line_id, headers=None):

        if headers is None:
            headers = RestApiHandler.default_headers

        url = RestApiHandler.base_url.format(host, port)
        request_url = "{}/api/line/{}".format(url, str(line_id))

        response = requests.get(url=request_url, timeout=30, headers=headers)
        if response.status_code == 200:
            return json.loads(response.content)

    """""
    get dashboard from server by of id
    """

    @staticmethod
    def get_dashboard_by_of_id(host, port, of_id, headers=None):

        if headers is None:
            headers = RestApiHandler.default_headers

        url = RestApiHandler.base_url.format(host, port)
        request_url = "{}/api/dashboardMonitoring/dashboard-monitoring-by-listen_on_postprocessing_shopfloordata-id/{}" \
            .format(url, str(of_id))

        response = requests.get(url=request_url, timeout=30, headers=headers)
        if response.status_code == 200:
            return json.loads(response.content)

    """""
    get dashboard from server by __affected_line id
    """

    @staticmethod
    def get_dashboard_by_line_id(host, port, line_id, headers=None):

        if headers is None:
            headers = RestApiHandler.default_headers

        url = RestApiHandler.base_url.format(host, port)
        request_url = "{}/api/dashboardMonitoring/dashboardMonitoringByLineId/{}"\
            .format(url, str(line_id))

        response = requests.get(url=request_url, timeout=30, headers=headers)
        if response.status_code == 200:
            return json.loads(response.content)

    """""
    get of from server by of id
    """

    @staticmethod
    def get_of_by_of_id(host, port, of_reference, headers=None):

        if headers is None:
            headers = RestApiHandler.default_headers

        url = RestApiHandler.base_url.format(host, port)
        request_url = "{}/api/listen_on_postprocessing_shopfloordata/by-listen_on_postprocessing_shopfloordata-id/{}" \
            .format(url, str(of_reference))

        response = requests.get(url=request_url, timeout=30, headers=headers)
        if response.status_code == 200:
            return json.loads(response.content)

    """""
    get panel from server by panel adresse mac
    """

    # TODO use reference instead of mac // should be updated in triki backend //
    #  get_panel_by_reference is not available in triki backend

    @staticmethod
    def get_panel_by_reference(host, port, reference, headers=None):

        if headers is None:
            headers = RestApiHandler.default_headers

        url = RestApiHandler.base_url.format(host, port)
        request_url = "{}/api/panel/byAdressMac/{}".format(url, str(reference))

        response = requests.get(url=request_url, timeout=30, headers=headers)
        if response.status_code == 200:
            return json.loads(response.content)

    @staticmethod
    def get_machine_by_id(host, port, machine_id, headers=None):

        if headers is None:
            headers = RestApiHandler.default_headers

        url = RestApiHandler.base_url.format(host, port)
        request_url = "{}/api/machine/{}".format(url, str(machine_id))

        response = requests.get(url=request_url, timeout=30, headers=headers)
        if response.status_code == 200:
            return json.loads(response.content)
