#!/usr/bin/python3
# -*- coding: utf-8 -*-
import asyncio
import httpx
import requests

from classes.Profile import Profile
from classes.account.WebsiteAccount import WebsiteAccount
from tools.Tool import Tool

from utils.datatypes import DataTypeInput
from utils.datatypes import DataTypeOutput
from utils.stdout import print_debug, print_error


class InstantUsernameTool(Tool):
    """
    Class which describe a InstantUsernameTool
    """
    deprecated = False

    def __init__(self):
        """The constructor of a InstantUsernameTool"""
        super().__init__()

    @staticmethod
    def get_config() -> dict[str]:
        """Function which return tool configuration as a dictionnary."""
        return {
            'active': True,
        }

    @staticmethod
    def get_lst_input_data_types() -> dict[str, bool]:
        """
        Function which return the list of data types which can be use to run this Tool.
        It's will help to make decision to run Tool depending on current data.
        """
        return {
            DataTypeInput.USERNAME: True,
        }

    @staticmethod
    def get_lst_output_data_types() -> list[str]:
        """
        Function which return the list of data types which can be receive by using this Tool.
        It's will help to make decision to complete profile to get more information.
        """
        return [
            DataTypeOutput.ACCOUNT,
        ]

    def execute(self):

        usernames = self.get_default_profile().get_lst_usernames()

        services: list[dict] = self.get_services()

        # Create a profile for each InstantUsername account found
        # because each account might be a different person
        for username in usernames:
            accounts: list = []
            accounts = asyncio.run(self.get_account_callback(services, username, accounts))

            for account in accounts:

                if account is None or account.get('available'):
                    print_debug("No account found on " + account.get('service') + " for " + username + ".")

                else:
                    service_name = account.get('service')
                    print_debug("Account found on " + service_name + " for " + username + ".")
                    url = account.get('url')

                    account = WebsiteAccount(
                        username=username,
                        website_name=service_name,
                        website_url=url
                    )

                    profile: Profile = self.get_default_profile().clone()
                    profile.set_lst_accounts([account])
                    self.append_profile(profile)

    def get_services(self) -> list:
        """
        Function to list services to check for username. It uses Instant Username Search API.
        """

        url = "https://api.instantusername.com/services"

        try:
            r = requests.get(url=url)
            res_json = r.json()
            print_debug("InstantUsername request succeed with a " + str(r.status_code) + " status code.")
        except Exception as e:
            print_error("[InstantUsernameTool:get_services] Request failed: " + str(e)[:100], True)
            return None

        return res_json

    async def request_service(self, client, service: dict, username: str):
        """
        Function to check a given username on a service. It uses Instant Username Search API.
        """

        service_name = service.get('service')
        endpoint: str = service.get('endpoint')

        if endpoint is None:
            return None
        else:
            endpoint = endpoint.format(username=username)

        url = "https://api.instantusername.com" + endpoint

        try:
            r = await client.get(url=url)
            res_json = r.json()
            print_debug("InstantUsername:" + service_name + " request succeed with a " + str(r.status_code) + " status code.")
        except Exception as e:
            print_error("[InstantUsernameTool:request_service] Request to " + service_name + " failed: " + str(e)[:100], True)
            return {
                "service": service_name,
                "endpoint": endpoint,
                "error": True,
                "message": str(e)
            }

        return res_json

    async def get_account_callback(self, lst_services: list[dict], username: str, lst_accounts: list) -> list:
        """ """
        async with httpx.AsyncClient() as client:
            lst_accounts = await asyncio.gather(*[self.request_service(client, service, username) for service in lst_services])
        print_debug("Finalized all. Return is a list of len {} outputs.".format(len(lst_accounts)))
        return lst_accounts
